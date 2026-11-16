from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("map", "0022_result_scenario_indexes")]

    operations = [AddIndexConcurrently(
        model_name="feature",
        index=models.Index(fields=["layer", "id"], name="features_layer_id_idx"),
    )]
