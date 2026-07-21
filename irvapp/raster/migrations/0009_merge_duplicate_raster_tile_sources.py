import json

from django.db import migrations


def merge_duplicate_raster_tile_sources(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    canonical_by_signature = {}
    duplicate_source_ids = []

    sources = RasterTileSource.objects.order_by("pk")
    for source in sources:
        signature = (
            source.database,
            source.description,
            json.dumps(source.keys, sort_keys=True, separators=(",", ":")),
        )

        canonical_source_id = canonical_by_signature.get(signature)
        if canonical_source_id is None:
            canonical_by_signature[signature] = source.pk
            continue

        Dataset.objects.filter(tile_source_id=source.pk).update(
            tile_source_id=canonical_source_id
        )
        duplicate_source_ids.append(source.pk)

    if duplicate_source_ids:
        RasterTileSource.objects.filter(pk__in=duplicate_source_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0012_dataset_quantity"),
        ("raster", "0008_remove_rastertilesource_domain"),
    ]

    operations = [
        migrations.RunPython(
            merge_duplicate_raster_tile_sources,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
