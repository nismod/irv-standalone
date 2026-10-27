import json
from math import ceil

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Count, Max, Min


TABLES = {
    "adaptationcostbenefit": ("adaptation_cost_benefit", ("rcp",), "adaptation"),
    "damagesexpected": ("damages_expected", ("rcp", "epoch"), "damages_expected"),
    "damagesnpv": ("damages_npv", ("rcp",), "damages_npv"),
    "damagesrp": ("damages_rp", ("rcp", "epoch"), "damages_rp"),
}


def backfill_parameters(apps, schema_editor):
    ParameterSet = apps.get_model("map", "ModelParameterSet")
    Parameter = apps.get_model("map", "ModelParameter")
    alias = schema_editor.connection.alias
    connection = schema_editor.connection
    quote = schema_editor.quote_name

    for model_name, (_, parameter_names, model_type) in TABLES.items():
        Model = apps.get_model("map", model_name)
        parameter_sets = []
        print(
            f"[map.0016] {Model._meta.db_table}: counting rows by parameter set",
            flush=True,
        )
        grouped_rows = Model.objects.using(alias).values(*parameter_names).annotate(
            _row_count=Count("feature_id")
        ).iterator()
        total_rows = 0
        for row in grouped_rows:
            values = {name: row[name] for name in parameter_names}
            total_rows += row["_row_count"]
            canonical_key = json.dumps(
                values, sort_keys=True, separators=(",", ":")
            )
            parameter_set, _ = ParameterSet.objects.using(alias).get_or_create(
                model_type=model_type,
                canonical_key=canonical_key,
            )
            Parameter.objects.using(alias).bulk_create(
                [
                    Parameter(
                        parameter_set=parameter_set,
                        name=name,
                        value=value,
                    )
                    for name, value in values.items()
                ],
                ignore_conflicts=True,
            )
            parameter_sets.append((values, parameter_set.pk))

        if not parameter_sets:
            print(f"[map.0016] {Model._meta.db_table}: no rows to backfill", flush=True)
            continue

        bounds = Model.objects.using(alias).aggregate(
            min_feature_id=Min("feature_id"),
            max_feature_id=Max("feature_id"),
        )
        min_feature_id = bounds["min_feature_id"]
        max_feature_id = bounds["max_feature_id"]
        feature_id_span = max_feature_id - min_feature_id + 1
        chunk_size = max(1, ceil(feature_id_span / 500))
        chunk_count = ceil(feature_id_span / chunk_size)
        report_every = max(1, chunk_count // 100)
        print(
            f"[map.0016] {Model._meta.db_table}: backfilling "
            f"{total_rows:,} rows across {len(parameter_sets)} parameter sets "
            f"in {chunk_count:,} feature-ID chunks",
            flush=True,
        )

        table = quote(Model._meta.db_table)
        parameter_columns = [
            Model._meta.get_field(name).column for name in parameter_names
        ]
        value_columns = parameter_columns + ["parameter_set_id"]
        source_alias = quote("parameter_values")
        target_alias = quote("result")
        source_columns = ", ".join(quote(column) for column in value_columns)
        casts = [
            Model._meta.get_field(name).db_type(connection)
            for name in parameter_names
        ] + ["bigint"]
        value_row = "(" + ", ".join(f"%s::{cast}" for cast in casts) + ")"
        values_clause = ", ".join(value_row for _ in parameter_sets)
        where_clause = " AND ".join(
            f"{target_alias}.{quote(column)} IS NOT DISTINCT FROM "
            f"{source_alias}.{quote(column)}"
            for column in parameter_columns
        )
        where_clause += (
            f" AND {target_alias}.{quote('feature_id')} > %s"
            f" AND {target_alias}.{quote('feature_id')} <= %s"
        )
        update_sql = (
            f"UPDATE {table} AS {target_alias} "
            f"SET {quote('parameter_set_id')} = "
            f"{source_alias}.{quote('parameter_set_id')} "
            f", {quote('id')} = nextval(%s::regclass) "
            f"FROM (VALUES {values_clause}) AS {source_alias} ({source_columns}) "
            f"WHERE {where_clause}"
        )
        parameters = [
            value
            for values, parameter_set_id in parameter_sets
            for value in [*(values[name] for name in parameter_names), parameter_set_id]
        ]
        sequence_name = f"{Model._meta.db_table}_id_seq"
        rows_updated = 0
        lower_bound = min_feature_id - 1
        for chunk_index in range(chunk_count):
            upper_bound = min(
                lower_bound + chunk_size,
                max_feature_id,
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    update_sql,
                    [sequence_name, *parameters, lower_bound, upper_bound],
                )
                rows_updated += cursor.rowcount
            if (
                (chunk_index + 1) % report_every == 0
                or chunk_index + 1 == chunk_count
            ):
                percent = rows_updated / total_rows * 100
                print(
                    f"[map.0016] {Model._meta.db_table}: "
                    f"{rows_updated:,}/{total_rows:,} rows ({percent:.1f}%)",
                    flush=True,
                )
            lower_bound = upper_bound


def reverse_backfill(apps, schema_editor):
    # Parameter data is retained when rolling back; the old columns are restored
    # by the reverse schema operations but their previous values cannot be
    # reconstructed after arbitrary parameter sets have been written.
    pass


REVERSE_SCHEMA_SQL = """
    ALTER TABLE adaptation_cost_benefit DROP CONSTRAINT adaptation_cost_benefit_pkey;
    ALTER TABLE adaptation_cost_benefit ADD COLUMN rcp varchar(8);
    UPDATE adaptation_cost_benefit AS result SET rcp = parameter.value #>> '{}'
      FROM model_parameter AS parameter
      WHERE parameter.parameter_set_id = result.parameter_set_id AND parameter.name = 'rcp';
    ALTER TABLE adaptation_cost_benefit ALTER COLUMN rcp SET NOT NULL;
    ALTER TABLE adaptation_cost_benefit ADD PRIMARY KEY (feature_id, hazard, rcp, adaptation_name, adaptation_protection_level);
    ALTER TABLE adaptation_cost_benefit DROP COLUMN id;

    ALTER TABLE damages_expected DROP CONSTRAINT damages_expected_pkey;
    ALTER TABLE damages_expected ADD COLUMN rcp varchar(8), ADD COLUMN epoch integer;
    UPDATE damages_expected AS result SET rcp = rcp_param.value #>> '{}', epoch = (epoch_param.value #>> '{}')::integer
      FROM model_parameter AS rcp_param, model_parameter AS epoch_param
      WHERE rcp_param.parameter_set_id = result.parameter_set_id AND rcp_param.name = 'rcp'
        AND epoch_param.parameter_set_id = result.parameter_set_id AND epoch_param.name = 'epoch';
    ALTER TABLE damages_expected ALTER COLUMN rcp SET NOT NULL, ALTER COLUMN epoch SET NOT NULL;
    ALTER TABLE damages_expected ADD PRIMARY KEY (feature_id, hazard, rcp, epoch, protection_standard);
    ALTER TABLE damages_expected DROP COLUMN id;

    ALTER TABLE damages_npv DROP CONSTRAINT damages_npv_pkey;
    ALTER TABLE damages_npv ADD COLUMN rcp varchar(8);
    UPDATE damages_npv AS result SET rcp = parameter.value #>> '{}'
      FROM model_parameter AS parameter
      WHERE parameter.parameter_set_id = result.parameter_set_id AND parameter.name = 'rcp';
    ALTER TABLE damages_npv ALTER COLUMN rcp SET NOT NULL;
    ALTER TABLE damages_npv ADD PRIMARY KEY (feature_id, hazard, rcp);
    ALTER TABLE damages_npv DROP COLUMN id;

    ALTER TABLE damages_rp DROP CONSTRAINT damages_rp_pkey;
    ALTER TABLE damages_rp ADD COLUMN rcp varchar(8), ADD COLUMN epoch integer;
    UPDATE damages_rp AS result SET rcp = rcp_param.value #>> '{}', epoch = (epoch_param.value #>> '{}')::integer
      FROM model_parameter AS rcp_param, model_parameter AS epoch_param
      WHERE rcp_param.parameter_set_id = result.parameter_set_id AND rcp_param.name = 'rcp'
        AND epoch_param.parameter_set_id = result.parameter_set_id AND epoch_param.name = 'epoch';
    ALTER TABLE damages_rp ALTER COLUMN rcp SET NOT NULL, ALTER COLUMN epoch SET NOT NULL;
    ALTER TABLE damages_rp ADD PRIMARY KEY (feature_id, hazard, rcp, epoch, rp);
    ALTER TABLE damages_rp DROP COLUMN id;
"""


class Migration(migrations.Migration):
    dependencies = [("map", "0015_network_layer_style")]

    operations = [
        migrations.CreateModel(
            name="ModelParameterSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model_type", models.CharField(max_length=32)),
                ("canonical_key", models.TextField()),
            ],
            options={
                "db_table": "model_parameter_set",
                "constraints": [models.UniqueConstraint(fields=("model_type", "canonical_key"), name="unique_model_parameter_set")],
            },
        ),
        migrations.CreateModel(
            name="ModelParameter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64)),
                ("value", models.JSONField()),
                ("parameter_set", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="parameters", to="map.modelparameterset")),
            ],
            options={
                "db_table": "model_parameter",
                "constraints": [models.UniqueConstraint(fields=("parameter_set", "name"), name="unique_parameter_name_per_set")],
            },
        ),
        migrations.AddField(
            model_name="adaptationcostbenefit",
            name="parameter_set",
            field=models.ForeignKey(db_index=False, null=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset"),
        ),
        migrations.AddField(
            model_name="damagesexpected",
            name="parameter_set",
            field=models.ForeignKey(db_index=False, null=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset"),
        ),
        migrations.AddField(
            model_name="damagesnpv",
            name="parameter_set",
            field=models.ForeignKey(db_index=False, null=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset"),
        ),
        migrations.AddField(
            model_name="damagesrp",
            name="parameter_set",
            field=models.ForeignKey(db_index=False, null=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset"),
        ),
        migrations.RunSQL(
            sql="""
                CREATE SEQUENCE adaptation_cost_benefit_id_seq;
                ALTER TABLE adaptation_cost_benefit ADD COLUMN id bigint;
                ALTER SEQUENCE adaptation_cost_benefit_id_seq OWNED BY adaptation_cost_benefit.id;
                ALTER TABLE adaptation_cost_benefit ALTER COLUMN id SET DEFAULT nextval('adaptation_cost_benefit_id_seq'::regclass);

                CREATE SEQUENCE damages_expected_id_seq;
                ALTER TABLE damages_expected ADD COLUMN id bigint;
                ALTER SEQUENCE damages_expected_id_seq OWNED BY damages_expected.id;
                ALTER TABLE damages_expected ALTER COLUMN id SET DEFAULT nextval('damages_expected_id_seq'::regclass);

                CREATE SEQUENCE damages_npv_id_seq;
                ALTER TABLE damages_npv ADD COLUMN id bigint;
                ALTER SEQUENCE damages_npv_id_seq OWNED BY damages_npv.id;
                ALTER TABLE damages_npv ALTER COLUMN id SET DEFAULT nextval('damages_npv_id_seq'::regclass);

                CREATE SEQUENCE damages_rp_id_seq;
                ALTER TABLE damages_rp ADD COLUMN id bigint;
                ALTER SEQUENCE damages_rp_id_seq OWNED BY damages_rp.id;
                ALTER TABLE damages_rp ALTER COLUMN id SET DEFAULT nextval('damages_rp_id_seq'::regclass);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunPython(backfill_parameters, reverse_backfill),
        migrations.RunSQL(
            sql="""
                ALTER TABLE adaptation_cost_benefit DROP CONSTRAINT adaptation_cost_benefit_pkey;
                ALTER TABLE adaptation_cost_benefit ADD PRIMARY KEY (id);
                ALTER TABLE adaptation_cost_benefit DROP COLUMN rcp;

                ALTER TABLE damages_expected DROP CONSTRAINT damages_expected_pkey;
                ALTER TABLE damages_expected ADD PRIMARY KEY (id);
                ALTER TABLE damages_expected DROP COLUMN rcp, DROP COLUMN epoch;

                ALTER TABLE damages_npv DROP CONSTRAINT damages_npv_pkey;
                ALTER TABLE damages_npv ADD PRIMARY KEY (id);
                ALTER TABLE damages_npv DROP COLUMN rcp;

                ALTER TABLE damages_rp DROP CONSTRAINT damages_rp_pkey;
                ALTER TABLE damages_rp ADD PRIMARY KEY (id);
                ALTER TABLE damages_rp DROP COLUMN rcp, DROP COLUMN epoch;
            """,
            reverse_sql=REVERSE_SCHEMA_SQL,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(model_name="adaptationcostbenefit", name="pk"),
                migrations.RemoveField(model_name="adaptationcostbenefit", name="rcp"),
                migrations.RemoveField(model_name="damagesexpected", name="pk"),
                migrations.RemoveField(model_name="damagesexpected", name="rcp"),
                migrations.RemoveField(model_name="damagesexpected", name="epoch"),
                migrations.RemoveField(model_name="damagesnpv", name="pk"),
                migrations.RemoveField(model_name="damagesnpv", name="rcp"),
                migrations.RemoveField(model_name="damagesrp", name="pk"),
                migrations.RemoveField(model_name="damagesrp", name="rcp"),
                migrations.RemoveField(model_name="damagesrp", name="epoch"),
                migrations.AddField(model_name="adaptationcostbenefit", name="id", field=models.BigAutoField(primary_key=True, serialize=False)),
                migrations.AddField(model_name="damagesexpected", name="id", field=models.BigAutoField(primary_key=True, serialize=False)),
                migrations.AddField(model_name="damagesnpv", name="id", field=models.BigAutoField(primary_key=True, serialize=False)),
                migrations.AddField(model_name="damagesrp", name="id", field=models.BigAutoField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.AlterField(model_name="adaptationcostbenefit", name="parameter_set", field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset")),
        migrations.AlterField(model_name="damagesexpected", name="parameter_set", field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset")),
        migrations.AlterField(model_name="damagesnpv", name="parameter_set", field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset")),
        migrations.AlterField(model_name="damagesrp", name="parameter_set", field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, to="map.modelparameterset")),
        migrations.AddConstraint(
            model_name="adaptationcostbenefit",
            constraint=models.UniqueConstraint(fields=("feature", "hazard", "parameter_set", "adaptation_name", "adaptation_protection_level"), name="unique_adaptation_result"),
        ),
        migrations.AddConstraint(
            model_name="damagesexpected",
            constraint=models.UniqueConstraint(fields=("feature", "hazard", "parameter_set", "protection_standard"), name="unique_expected_damage_result"),
        ),
        migrations.AddConstraint(
            model_name="damagesnpv",
            constraint=models.UniqueConstraint(fields=("feature", "hazard", "parameter_set"), name="unique_npv_damage_result"),
        ),
        migrations.AddConstraint(
            model_name="damagesrp",
            constraint=models.UniqueConstraint(fields=("feature", "hazard", "parameter_set", "rp"), name="unique_return_period_damage_result"),
        ),
    ]
