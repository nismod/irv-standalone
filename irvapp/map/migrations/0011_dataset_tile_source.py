import django.db.models.deletion
from django.db import migrations, models


def move_tile_source_relationship(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    datasets_by_id = Dataset.objects.in_bulk()
    datasets_to_update = []
    for source in RasterTileSource.objects.exclude(
        dataset__isnull=True
    ).order_by("pk"):
        dataset = datasets_by_id[source.dataset_id]
        if (
            dataset.tile_source_id is not None
            and dataset.tile_source_id != source.pk
        ):
            raise RuntimeError(
                f"Dataset {dataset.pk!r} is linked to multiple tile sources"
            )
        dataset.tile_source_id = source.pk
        datasets_to_update.append(dataset)

    Dataset.objects.bulk_update(datasets_to_update, ["tile_source"])


def restore_tile_source_relationship(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    datasets = Dataset.objects.exclude(tile_source__isnull=True).order_by("pk")
    datasets_by_source_id = {}
    for dataset in datasets:
        if dataset.tile_source_id in datasets_by_source_id:
            raise RuntimeError(
                "Cannot reverse the tile-source relationship because tile "
                f"source {dataset.tile_source_id!r} has multiple datasets"
            )
        datasets_by_source_id[dataset.tile_source_id] = dataset.pk

    sources = list(
        RasterTileSource.objects.filter(pk__in=datasets_by_source_id)
    )
    for source in sources:
        source.dataset_id = datasets_by_source_id[source.pk]
    RasterTileSource.objects.bulk_update(sources, ["dataset"])


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0010_dataset_license"),
        ("raster", "0006_remove_rastertilesource_name_and_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="tile_source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="datasets",
                to="raster.rastertilesource",
            ),
        ),
        migrations.RunPython(
            move_tile_source_relationship,
            reverse_code=restore_tile_source_relationship,
        ),
    ]
