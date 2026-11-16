import django.db.models.deletion
from django.db import migrations, models

import map.models.risk


class Migration(migrations.Migration):
    dependencies = [("map", "0015_network_layer_style")]

    operations = [
        migrations.CreateModel(
            name="ModelParameterSet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("model_type", models.CharField(max_length=32)),
                ("canonical_key", models.TextField()),
            ],
            options={
                "db_table": "model_parameter_set",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("model_type", "canonical_key"),
                        name="unique_model_parameter_set",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ModelParameter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=64)),
                ("value", models.JSONField()),
                (
                    "parameter_set",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parameters",
                        to="map.modelparameterset",
                    ),
                ),
            ],
            options={
                "db_table": "model_parameter",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("parameter_set", "name"),
                        name="unique_parameter_name_per_set",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="adaptationcostbenefit",
            name="parameter_set",
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="map.modelparameterset",
            ),
        ),
        migrations.AddField(
            model_name="damagesexpected",
            name="parameter_set",
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="map.modelparameterset",
            ),
        ),
        migrations.AddField(
            model_name="damagesnpv",
            name="parameter_set",
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="map.modelparameterset",
            ),
        ),
        migrations.AddField(
            model_name="damagesrp",
            name="parameter_set",
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="map.modelparameterset",
            ),
        ),
        migrations.RunSQL(
            sql="""
                CREATE SEQUENCE adaptation_cost_benefit_id_seq;
                ALTER TABLE adaptation_cost_benefit ADD COLUMN id bigint;
                ALTER TABLE adaptation_cost_benefit
                    ALTER COLUMN id SET DEFAULT nextval('adaptation_cost_benefit_id_seq'::regclass);
                ALTER SEQUENCE adaptation_cost_benefit_id_seq
                    OWNED BY adaptation_cost_benefit.id;

                CREATE SEQUENCE damages_expected_id_seq;
                ALTER TABLE damages_expected ADD COLUMN id bigint;
                ALTER TABLE damages_expected
                    ALTER COLUMN id SET DEFAULT nextval('damages_expected_id_seq'::regclass);
                ALTER SEQUENCE damages_expected_id_seq
                    OWNED BY damages_expected.id;

                CREATE SEQUENCE damages_npv_id_seq;
                ALTER TABLE damages_npv ADD COLUMN id bigint;
                ALTER TABLE damages_npv
                    ALTER COLUMN id SET DEFAULT nextval('damages_npv_id_seq'::regclass);
                ALTER SEQUENCE damages_npv_id_seq OWNED BY damages_npv.id;

                CREATE SEQUENCE damages_rp_id_seq;
                ALTER TABLE damages_rp ADD COLUMN id bigint;
                ALTER TABLE damages_rp
                    ALTER COLUMN id SET DEFAULT nextval('damages_rp_id_seq'::regclass);
                ALTER SEQUENCE damages_rp_id_seq OWNED BY damages_rp.id;
            """,
            reverse_sql="""
                ALTER TABLE adaptation_cost_benefit DROP COLUMN id;
                ALTER TABLE damages_expected DROP COLUMN id;
                ALTER TABLE damages_npv DROP COLUMN id;
                ALTER TABLE damages_rp DROP COLUMN id;
            """,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="adaptationcostbenefit",
                    name="id",
                    field=models.BigIntegerField(
                        db_default=map.models.risk.SequenceNextValue(
                            "adaptation_cost_benefit_id_seq"
                        ),
                        editable=False,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name="damagesexpected",
                    name="id",
                    field=models.BigIntegerField(
                        db_default=map.models.risk.SequenceNextValue(
                            "damages_expected_id_seq"
                        ),
                        editable=False,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name="damagesnpv",
                    name="id",
                    field=models.BigIntegerField(
                        db_default=map.models.risk.SequenceNextValue(
                            "damages_npv_id_seq"
                        ),
                        editable=False,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name="damagesrp",
                    name="id",
                    field=models.BigIntegerField(
                        db_default=map.models.risk.SequenceNextValue(
                            "damages_rp_id_seq"
                        ),
                        editable=False,
                        null=True,
                    ),
                ),
            ],
        ),
    ]
