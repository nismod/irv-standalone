from django.db import migrations, models


def restore_dataset_quantities(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    RasterLayer = apps.get_model("map", "RasterLayer")
    alias = schema_editor.connection.alias
    for dataset in Dataset.objects.using(alias).iterator():
        values = set(RasterLayer.objects.using(alias).filter(dataset_id=dataset.pk).values_list("quantity", "unit"))
        if len(values) > 1:
            raise RuntimeError(f"Cannot reverse: raster layers in dataset {dataset.pk!r} have different quantities or units.")
        if values:
            quantity, unit = values.pop()
            Dataset.objects.using(alias).filter(pk=dataset.pk).update(quantity=quantity, unit=unit)


class Migration(migrations.Migration):
    dependencies = [("map", "0029_remove_dataset_display_order_and_more")]

    operations = [
        migrations.AlterField(model_name="dataset", name="quantity", field=models.CharField(default="")),
        migrations.AlterField(model_name="dataset", name="unit", field=models.CharField(default="")),
        migrations.RunPython(migrations.RunPython.noop, restore_dataset_quantities),
        migrations.RemoveField(model_name="dataset", name="quantity"),
        migrations.RemoveField(model_name="dataset", name="unit"),
    ]
