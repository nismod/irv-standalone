from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("map", "0021_unique_result_ids")]

    operations = [
        AddIndexConcurrently(
            model_name="damagesexpected",
            index=models.Index(
                fields=["parameter_set", "hazard", "protection_standard", "feature"],
                name="damages_expected_scenario_idx",
            ),
        ),
        AddIndexConcurrently(
            model_name="adaptationcostbenefit",
            index=models.Index(
                fields=["parameter_set", "hazard", "adaptation_name", "adaptation_protection_level", "feature"],
                name="adaptation_scenario_idx",
            ),
        ),
    ]
