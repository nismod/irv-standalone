from django.db import migrations


def restore_dataset_colours(apps, schema_editor):
    Dataset = apps.get_model("map", "Dataset")
    RasterLayer = apps.get_model("map", "RasterLayer")
    alias = schema_editor.connection.alias
    # Only the original one-layer-per-dataset layout can be reversed through
    # migration 0027. Restore its colours for 0027's loss-prevention check.
    for layer in RasterLayer.objects.using(alias).filter(id__in=Dataset.objects.using(alias).values("id")):
        if layer.pk == layer.dataset_id:
            Dataset.objects.using(alias).filter(pk=layer.dataset_id).update(
                color_scheme=layer.color_scheme, color_range=layer.color_range,
            )


class Migration(migrations.Migration):
    dependencies = [("map", "0027_remove_dataset_tile_source_rasterlayer")]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, restore_dataset_colours),
        migrations.RemoveField(model_name="dataset", name="color_scheme"),
        migrations.RemoveField(model_name="dataset", name="color_range"),
    ]
