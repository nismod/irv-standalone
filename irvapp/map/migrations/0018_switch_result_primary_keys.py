import django.db.models.deletion
from django.db import migrations, models


REVERSE_SCHEMA_SQL = """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM adaptation_cost_benefit AS result
            WHERE NOT EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name = 'rcp'
            ) OR EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name <> 'rcp'
            )
        ) OR EXISTS (
            SELECT 1 FROM damages_expected AS result
            WHERE NOT EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name = 'rcp'
            ) OR NOT EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name = 'epoch'
            ) OR EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name NOT IN ('rcp', 'epoch')
            )
        ) OR EXISTS (
            SELECT 1 FROM damages_npv AS result
            WHERE NOT EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name = 'rcp'
            ) OR EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name <> 'rcp'
            )
        ) OR EXISTS (
            SELECT 1 FROM damages_rp AS result
            WHERE NOT EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name = 'rcp'
            ) OR NOT EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name = 'epoch'
            ) OR EXISTS (
                SELECT 1 FROM model_parameter AS parameter
                WHERE parameter.parameter_set_id = result.parameter_set_id
                  AND parameter.name NOT IN ('rcp', 'epoch')
            )
        ) THEN
            RAISE EXCEPTION 'Cannot reverse flexible model parameters: result rows contain parameters that legacy columns cannot represent.';
        END IF;
    END $$;

    ALTER TABLE adaptation_cost_benefit ADD COLUMN rcp varchar(8);
    UPDATE adaptation_cost_benefit AS result SET rcp = parameter.value #>> '{}'
      FROM model_parameter AS parameter
      WHERE parameter.parameter_set_id = result.parameter_set_id AND parameter.name = 'rcp';
    ALTER TABLE adaptation_cost_benefit ALTER COLUMN rcp SET NOT NULL;

    ALTER TABLE damages_expected ADD COLUMN rcp varchar(8), ADD COLUMN epoch integer;
    UPDATE damages_expected AS result SET rcp = rcp_param.value #>> '{}', epoch = (epoch_param.value #>> '{}')::integer
      FROM model_parameter AS rcp_param, model_parameter AS epoch_param
      WHERE rcp_param.parameter_set_id = result.parameter_set_id AND rcp_param.name = 'rcp'
        AND epoch_param.parameter_set_id = result.parameter_set_id AND epoch_param.name = 'epoch';
    ALTER TABLE damages_expected ALTER COLUMN rcp SET NOT NULL, ALTER COLUMN epoch SET NOT NULL;

    ALTER TABLE damages_npv ADD COLUMN rcp varchar(8);
    UPDATE damages_npv AS result SET rcp = parameter.value #>> '{}'
      FROM model_parameter AS parameter
      WHERE parameter.parameter_set_id = result.parameter_set_id AND parameter.name = 'rcp';
    ALTER TABLE damages_npv ALTER COLUMN rcp SET NOT NULL;

    ALTER TABLE damages_rp ADD COLUMN rcp varchar(8), ADD COLUMN epoch integer;
    UPDATE damages_rp AS result SET rcp = rcp_param.value #>> '{}', epoch = (epoch_param.value #>> '{}')::integer
      FROM model_parameter AS rcp_param, model_parameter AS epoch_param
      WHERE rcp_param.parameter_set_id = result.parameter_set_id AND rcp_param.name = 'rcp'
        AND epoch_param.parameter_set_id = result.parameter_set_id AND epoch_param.name = 'epoch';
    ALTER TABLE damages_rp ALTER COLUMN rcp SET NOT NULL, ALTER COLUMN epoch SET NOT NULL;

    ALTER TABLE adaptation_cost_benefit
      ADD CONSTRAINT adaptation_cost_benefit_pkey
      PRIMARY KEY (feature_id, hazard, rcp, adaptation_name, adaptation_protection_level);
    ALTER TABLE damages_expected
      ADD CONSTRAINT damages_expected_pkey
      PRIMARY KEY (feature_id, hazard, rcp, epoch, protection_standard);
    ALTER TABLE damages_npv
      ADD CONSTRAINT damages_npv_pkey PRIMARY KEY (feature_id, hazard, rcp);
    ALTER TABLE damages_rp
      ADD CONSTRAINT damages_rp_pkey PRIMARY KEY (feature_id, hazard, rcp, epoch, rp);
"""


def add_drop_column_operations():
    return [
        migrations.RunSQL(
            "ALTER TABLE adaptation_cost_benefit DROP CONSTRAINT IF EXISTS adaptation_cost_benefit_pkey;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE damages_expected DROP CONSTRAINT IF EXISTS damages_expected_pkey;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE damages_npv DROP CONSTRAINT IF EXISTS damages_npv_pkey;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE damages_rp DROP CONSTRAINT IF EXISTS damages_rp_pkey;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE adaptation_cost_benefit DROP COLUMN IF EXISTS rcp;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE damages_expected DROP COLUMN IF EXISTS rcp, DROP COLUMN IF EXISTS epoch;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE damages_npv DROP COLUMN IF EXISTS rcp;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE damages_rp DROP COLUMN IF EXISTS rcp, DROP COLUMN IF EXISTS epoch;",
            reverse_sql=REVERSE_SCHEMA_SQL,
        ),
    ]


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("map", "0017_backfill_model_parameters")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=add_drop_column_operations(),
            state_operations=[
                migrations.RemoveField(
                    model_name="adaptationcostbenefit", name="pk"
                ),
                migrations.RemoveField(
                    model_name="damagesexpected", name="pk"
                ),
                migrations.RemoveField(model_name="damagesnpv", name="pk"),
                migrations.RemoveField(model_name="damagesrp", name="pk"),
                migrations.RemoveField(
                    model_name="adaptationcostbenefit", name="rcp"
                ),
                migrations.RemoveField(model_name="damagesexpected", name="rcp"),
                migrations.RemoveField(
                    model_name="damagesexpected", name="epoch"
                ),
                migrations.RemoveField(model_name="damagesnpv", name="rcp"),
                migrations.RemoveField(model_name="damagesrp", name="rcp"),
                migrations.RemoveField(model_name="damagesrp", name="epoch"),
                migrations.AddField(
                    model_name="adaptationcostbenefit",
                    name="pk",
                    field=models.CompositePrimaryKey(
                        "parameter_set_id",
                        "feature_id",
                        "hazard",
                        "adaptation_name",
                        "adaptation_protection_level",
                        blank=True,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AddField(
                    model_name="damagesexpected",
                    name="pk",
                    field=models.CompositePrimaryKey(
                        "parameter_set_id",
                        "feature_id",
                        "hazard",
                        "protection_standard",
                        blank=True,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AddField(
                    model_name="damagesnpv",
                    name="pk",
                    field=models.CompositePrimaryKey(
                        "parameter_set_id",
                        "feature_id",
                        "hazard",
                        blank=True,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AddField(
                    model_name="damagesrp",
                    name="pk",
                    field=models.CompositePrimaryKey(
                        "parameter_set_id",
                        "feature_id",
                        "hazard",
                        "rp",
                        blank=True,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="adaptationcostbenefit",
                    name="parameter_set",
                    field=models.ForeignKey(
                        db_index=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="map.modelparameterset",
                    ),
                ),
                migrations.AlterField(
                    model_name="damagesexpected",
                    name="parameter_set",
                    field=models.ForeignKey(
                        db_index=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="map.modelparameterset",
                    ),
                ),
                migrations.AlterField(
                    model_name="damagesnpv",
                    name="parameter_set",
                    field=models.ForeignKey(
                        db_index=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="map.modelparameterset",
                    ),
                ),
                migrations.AlterField(
                    model_name="damagesrp",
                    name="parameter_set",
                    field=models.ForeignKey(
                        db_index=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="map.modelparameterset",
                    ),
                ),
            ],
        )
    ]
