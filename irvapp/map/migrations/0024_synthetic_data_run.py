from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("map", "0023_feature_layer_id_index")]

    operations = [
        migrations.CreateModel(
            name="SyntheticDataRun",
            fields=[
                (
                    "name",
                    models.CharField(primary_key=True, max_length=64, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("config", models.JSONField()),
                ("result_ids", models.JSONField(default=dict)),
                ("parameter_set_ids", models.JSONField(default=list)),
            ],
            options={"db_table": "synthetic_data_runs"},
        ),
    ]
