from django.db import migrations


def seed_currency(apps, schema_editor):
    MapConfig = apps.get_model("map", "MapConfig")
    MapConfig.objects.get_or_create(
        config_name="currency",
        defaults={"config_value": "JMD", "config_type": "string"},
    )


def unseed_currency(apps, schema_editor):
    MapConfig = apps.get_model("map", "MapConfig")
    MapConfig.objects.filter(
        config_name="currency", config_value="JMD", config_type="string"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("map", "0021_unique_result_ids")]

    operations = [migrations.RunPython(seed_currency, unseed_currency)]
