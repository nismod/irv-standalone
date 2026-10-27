import json
from math import ceil

from django.db import migrations
from django.db.models import Count, Max, Min


TABLES = {
    "adaptationcostbenefit": (
        "adaptation_cost_benefit",
        ("rcp",),
        "adaptation",
    ),
    "damagesexpected": (
        "damages_expected",
        ("rcp", "epoch"),
        "damages_expected",
    ),
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
        table_name = Model._meta.db_table
        print(
            f"[map.0017] {table_name}: counting rows by parameter set",
            flush=True,
        )
        grouped_rows = (
            Model.objects.using(alias)
            .values(*parameter_names)
            .annotate(_row_count=Count("feature_id"))
            .iterator()
        )
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
            print(f"[map.0017] {table_name}: no rows to backfill", flush=True)
            continue

        already_backfilled = Model.objects.using(alias).filter(
            parameter_set_id__isnull=False
        ).count()
        if already_backfilled == total_rows:
            print(
                f"[map.0017] {table_name}: already complete "
                f"({total_rows:,}/{total_rows:,} rows)",
                flush=True,
            )
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
            f"[map.0017] {table_name}: resuming backfill at "
            f"{already_backfilled:,}/{total_rows:,} rows; processing "
            f"{chunk_count:,} feature-ID chunks",
            flush=True,
        )

        table = quote(table_name)
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
            f" AND {target_alias}.{quote('parameter_set_id')} IS NULL"
            f" AND {target_alias}.{quote('feature_id')} > %s"
            f" AND {target_alias}.{quote('feature_id')} <= %s"
        )
        update_sql = (
            f"UPDATE {table} AS {target_alias} "
            f"SET {quote('parameter_set_id')} = "
            f"{source_alias}.{quote('parameter_set_id')}, "
            f"{quote('id')} = nextval(%s::regclass) "
            f"FROM (VALUES {values_clause}) AS {source_alias} ({source_columns}) "
            f"WHERE {where_clause}"
        )
        parameters = [
            value
            for values, parameter_set_id in parameter_sets
            for value in [
                *(values[name] for name in parameter_names),
                parameter_set_id,
            ]
        ]
        sequence_name = f"{table_name}_id_seq"
        completed_rows = already_backfilled
        lower_bound = min_feature_id - 1
        for chunk_index in range(chunk_count):
            upper_bound = min(lower_bound + chunk_size, max_feature_id)
            with connection.cursor() as cursor:
                cursor.execute(
                    update_sql,
                    [sequence_name, *parameters, lower_bound, upper_bound],
                )
                completed_rows += cursor.rowcount
            if (
                (chunk_index + 1) % report_every == 0
                or chunk_index + 1 == chunk_count
            ):
                percent = completed_rows / total_rows * 100
                print(
                    f"[map.0017] {table_name}: "
                    f"{completed_rows:,}/{total_rows:,} rows ({percent:.1f}%)",
                    flush=True,
                )
            lower_bound = upper_bound

        if completed_rows != total_rows:
            raise RuntimeError(
                f"Backfill incomplete for {table_name}: "
                f"{completed_rows:,}/{total_rows:,} rows have parameters. "
                "Rerun this migration to resume."
            )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("map", "0016_flexible_model_parameters")]

    operations = [migrations.RunPython(backfill_parameters, migrations.RunPython.noop)]
