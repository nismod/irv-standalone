from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0011_dataset_tile_source"),
        ("raster", "0006_remove_rastertilesource_name_and_group"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rastertilesource",
            name="dataset",
        ),
    ]
