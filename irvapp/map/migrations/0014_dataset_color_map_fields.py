from django.db import migrations, models


HAZARD_COLOR_DEFAULTS = {
    "fluvial": {"color_scheme": "blues", "color_range": [0, 10]},
    "coastal": {"color_scheme": "greens", "color_range": [0, 10]},
    "surface": {"color_scheme": "purples", "color_range": [0, 10]},
    "pluvial": {"color_scheme": "purples", "color_range": [0, 10]},
    "cyclone": {"color_scheme": "reds", "color_range": [0, 75]},
    "storm": {"color_scheme": "viridis", "color_range": [0, 250]},
}


def populate_hazard_color_defaults(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")

    for dataset_id, defaults in HAZARD_COLOR_DEFAULTS.items():
        Dataset.objects.filter(pk=dataset_id).update(**defaults)


def clear_hazard_color_defaults(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    Dataset.objects.filter(pk__in=HAZARD_COLOR_DEFAULTS.keys()).update(
        color_scheme=None,
        color_range=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0013_mapconfig_initial_values"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="color_scheme",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="dataset",
            name="color_range",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.RunPython(
            populate_hazard_color_defaults,
            reverse_code=clear_hazard_color_defaults,
        ),
    ]
