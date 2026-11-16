from django.db import migrations


def add_primary_key(table, columns):
    constraint = f"{table}_pkey"
    column_sql = ", ".join(columns)
    return migrations.RunSQL(
        sql=f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conrelid = '{table}'::regclass AND contype = 'p'
                ) THEN
                    ALTER TABLE {table}
                    ADD CONSTRAINT {constraint} PRIMARY KEY ({column_sql});
                END IF;
            END $$;
        """,
        reverse_sql=(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint};"
        ),
    )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("map", "0018_switch_result_primary_keys")]

    operations = [
        add_primary_key(
            "adaptation_cost_benefit",
            (
                "parameter_set_id",
                "feature_id",
                "hazard",
                "adaptation_name",
                "adaptation_protection_level",
            ),
        ),
        add_primary_key(
            "damages_expected",
            (
                "parameter_set_id",
                "feature_id",
                "hazard",
                "protection_standard",
            ),
        ),
        add_primary_key(
            "damages_npv",
            ("parameter_set_id", "feature_id", "hazard"),
        ),
        add_primary_key(
            "damages_rp",
            ("parameter_set_id", "feature_id", "hazard", "rp"),
        ),
    ]
