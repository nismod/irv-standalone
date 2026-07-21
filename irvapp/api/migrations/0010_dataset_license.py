from django.db import migrations, models


def copy_source_licenses_to_datasets(apps, schema_editor):
    Dataset = apps.get_model("api", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    source_rows = (
        RasterTileSource.objects.exclude(dataset__isnull=True)
        .exclude(license__isnull=True)
        .exclude(license="")
        .values("dataset_id", "license")
        .order_by("pk")
    )

    dataset_license_by_id = {}
    for row in source_rows:
        dataset_license_by_id.setdefault(row["dataset_id"], row["license"])

    datasets = list(
        Dataset.objects.filter(
            pk__in=dataset_license_by_id.keys(),
            license__isnull=True,
        )
    )
    for dataset in datasets:
        dataset.license = dataset_license_by_id[dataset.pk]
    Dataset.objects.bulk_update(datasets, ["license"])

def copy_dataset_licenses_to_sources(apps, schema_editor):
    Dataset = apps.get_model("api", "Dataset")
    RasterTileSource = apps.get_model("raster", "RasterTileSource")

    for dataset in Dataset.objects.exclude(license__isnull=True):
        RasterTileSource.objects.filter(dataset_id=dataset.pk).update(
            license=dataset.license
        )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_dataset_access_groups"),
        ("raster", "0004_rastertilesource_dataset"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="license",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
            ),
        ),
        migrations.RunPython(
            copy_source_licenses_to_datasets,
            reverse_code=copy_dataset_licenses_to_sources,
        ),
    ]
