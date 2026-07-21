from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("raster", "0007_remove_rastertilesource_dataset"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rastertilesource",
            name="domain",
        ),
    ]
