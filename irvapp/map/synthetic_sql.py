"""Set-based generation for full-network development fixtures."""

import json

from django.db import connection


def insert_fixtures(model, model_type, features, scenarios, seed, adaptations):
    """Insert a feature batch and return exact, compact ownership intervals.

    Consecutive returned IDs are grouped in SQL, so even a large run does not
    need one Python integer or JSON entry for every generated result row.
    Gaps caused by existing keys or concurrent inserts are never claimed.
    """
    quote = connection.ops.quote_name
    dimensions = {
        "damages_expected": ["protection_standard"],
        "damages_rp": ["rp", "exposure"],
        "adaptation": [
            "adaptation_name",
            "adaptation_protection_level",
            "protector_feature_id",
            "adaptation_cost",
        ],
    }[model_type]
    means = {
        "damages_expected": ["ead", "eael"],
        "damages_rp": ["damage", "loss"],
        "adaptation": ["avoided_ead", "avoided_eael"],
    }[model_type]
    columns = ["parameter_set_id", "feature_id", "hazard", *dimensions]
    expressions = list(columns)
    for name in means:
        columns.extend([name + "_amin", name + "_mean", name + "_amax"])
        expressions.extend(
            [
                f"round(({name} * 0.7)::numeric, 2)",
                name,
                f"round(({name} * 1.3)::numeric, 2)",
            ]
        )

    computed = {
        "damages_expected": """
            SELECT metrics.*, standard AS protection_standard,
                round((annual * fraction)::numeric, 2) AS ead,
                round((annual * 0.35 * fraction)::numeric, 2) AS eael
            FROM metrics CROSS JOIN (VALUES (0, 1.0), (100, 0.6)) AS protection(standard, fraction)
        """,
        "damages_rp": """
            SELECT period_values.*, round((damage * 0.35)::numeric, 2) AS loss,
                CASE WHEN damage IS NULL THEN NULL WHEN damage = 0 THEN 0 ELSE 1 END AS exposure
            FROM (
                SELECT metrics.*, rp,
                    CASE WHEN position %% 10 = 9 THEN NULL
                        WHEN position %% 10 = 8 THEN 0
                        ELSE round((amount * severity * power(rp::float8 / max_rp, 0.4))::numeric, 2)
                    END AS damage
                FROM metrics CROSS JOIN LATERAL unnest(return_periods) AS periods(rp)
            ) AS period_values
        """,
        "adaptation": """
            SELECT metrics.*, option.name AS adaptation_name,
                option.level AS adaptation_protection_level,
                protector_id AS protector_feature_id,
                round((amount * 0.08)::numeric, 2) AS adaptation_cost,
                round((annual * option.fraction)::numeric, 2) AS avoided_ead,
                round((annual * 0.35 * option.fraction)::numeric, 2) AS avoided_eael
            FROM metrics CROSS JOIN unnest(
                %(adaptation_names)s::text[], %(adaptation_levels)s::float8[], %(adaptation_fractions)s::float8[]
            ) AS option(name, level, fraction)
        """,
    }[model_type]
    conflict_columns = [
        model._meta.get_field(name).column for name in model._meta.pk.field_names
    ]
    sql = f"""
        WITH features AS (
            SELECT * FROM unnest(%(ids)s::bigint[], %(positions)s::int[], %(protectors)s::int[])
                AS selected(feature_id, position, protector_id)
        ), scenarios AS (
            SELECT parameter_set_id, hazard, severity, annual_factor,
                ARRAY(SELECT jsonb_array_elements_text(periods)::int) AS return_periods,
                (SELECT max(value::float8) FROM jsonb_array_elements_text(periods) AS period(value)) AS max_rp
            FROM jsonb_to_recordset(%(scenarios)s::jsonb) AS scenario(
                parameter_set_id bigint, hazard text, severity float8, annual_factor float8, periods jsonb
            )
        ), base AS MATERIALIZED (
            SELECT features.*, scenarios.*,
                power(10::float8, 4 + 3 * (
                    ('x' || substr(md5(%(seed_prefix)s || feature_id::text || ':' || hazard), 1, 8))::bit(32)::bigint
                    / 4294967295.0
                )::float8) AS amount
            FROM features CROSS JOIN scenarios
        ), metrics AS MATERIALIZED (
            SELECT base.*,
                CASE WHEN position %% 10 = 9 THEN NULL WHEN position %% 10 = 8 THEN 0
                    ELSE round((amount * severity * annual_factor)::numeric, 2) END AS annual
            FROM base
        ), computed AS ({computed}), inserted AS (
            INSERT INTO {quote(model._meta.db_table)} ({', '.join(map(quote, columns))})
            SELECT {', '.join(expressions)} FROM computed
            ON CONFLICT ({', '.join(map(quote, conflict_columns))}) DO NOTHING
            RETURNING id
        ), numbered AS (
            SELECT id, id - row_number() OVER (ORDER BY id) AS ownership_group FROM inserted
        )
        SELECT min(id), max(id), count(*) FROM numbered GROUP BY ownership_group ORDER BY min(id)
    """
    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            {
                "ids": [item[0] for item in features],
                "positions": [item[1] for item in features],
                "protectors": [item[2] for item in features],
                "scenarios": json.dumps(scenarios),
                "seed_prefix": f"{seed}:values:",
                "adaptation_names": [item[0] for item in adaptations],
                "adaptation_levels": [item[1] for item in adaptations],
                "adaptation_fractions": [item[2] for item in adaptations],
            },
        )
        return cursor.fetchall()
