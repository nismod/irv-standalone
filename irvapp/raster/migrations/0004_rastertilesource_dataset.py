import django.db.models.deletion
from django.db import migrations, models


def link_sources_to_datasets(apps, schema_editor):
    Dataset = apps.get_model("api", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    datasets_by_id = Dataset.objects.in_bulk()
    for source in RasterTileSource.objects.filter(dataset__isnull=True):
        dataset = datasets_by_id.get(source.domain)
        if dataset is not None:
            source.dataset = dataset
            source.save(update_fields=["dataset"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_dataset_access_groups"),
        ("raster", "0003_split_hazard_sources"),
    ]

    operations = [
        migrations.AddField(
            model_name="rastertilesource",
            name="dataset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="raster_tile_sources",
                to="api.dataset",
            ),
        ),
        migrations.RunPython(
            link_sources_to_datasets,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
