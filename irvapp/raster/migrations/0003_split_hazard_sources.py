from django.db import migrations


def split_hazard_source(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    try:
        hazard_source = RasterTileSource.objects.get(domain="hazards")
    except RasterTileSource.DoesNotExist:
        # New databases may have their tile sources loaded after migrations.
        return

    source_values = {
        "description": hazard_source.description,
        "license": hazard_source.license,
        "keys": hazard_source.keys,
        "database": hazard_source.database,
    }

    datasets = list(Dataset.objects.filter(group__iexact="hazards"))
    if not datasets:
        return

    for dataset in datasets:
        RasterTileSource.objects.update_or_create(
            domain=dataset.pk,
            defaults={
                **source_values,
                "name": dataset.label,
                "group": dataset.group,
            },
        )

    hazard_source.delete()


def combine_hazard_sources(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    hazard_ids = list(
        Dataset.objects.filter(group__iexact="hazards").values_list(
            "pk", flat=True
        )
    )
    hazard_sources = RasterTileSource.objects.filter(domain__in=hazard_ids)
    source = hazard_sources.first()
    if source is None:
        return

    RasterTileSource.objects.update_or_create(
        domain="hazards",
        defaults={
            "name": "Hazards",
            "group": source.group,
            "description": source.description,
            "license": source.license,
            "keys": source.keys,
            "database": source.database,
        },
    )
    hazard_sources.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0008_mapconfig_config_type"),
        ("raster", "0002_rastertilesource_database"),
    ]

    operations = [
        migrations.RunPython(
            split_hazard_source,
            reverse_code=combine_hazard_sources,
        ),
    ]
