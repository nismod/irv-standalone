from django.db import migrations


INITIAL_MAP_CONFIG = (
    ("appName", "J-SRAT", "string"),
    ("latitude", "18.14", "number"),
    ("longitude", "-77.28", "number"),
    ("zoom", "9", "number"),
    ("minZoom", "3", "number"),
    ("maxZoom", "16", "number"),
    ("pitch", "0", "number"),
)


def seed_map_config(apps, schema_editor):
    MapConfig = apps.get_model("map", "MapConfig")

    for config_name, config_value, config_type in INITIAL_MAP_CONFIG:
        MapConfig.objects.get_or_create(
            config_name=config_name,
            defaults={
                "config_value": config_value,
                "config_type": config_type,
            },
        )


def unseed_map_config(apps, schema_editor):
    MapConfig = apps.get_model("map", "MapConfig")

    for config_name, config_value, config_type in INITIAL_MAP_CONFIG:
        MapConfig.objects.filter(
            config_name=config_name,
            config_value=config_value,
            config_type=config_type,
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0012_dataset_quantity"),
    ]

    operations = [
        migrations.RunPython(seed_map_config, unseed_map_config),
    ]
