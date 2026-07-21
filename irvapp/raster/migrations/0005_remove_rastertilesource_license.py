from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_dataset_license"),
        ("raster", "0004_rastertilesource_dataset"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rastertilesource",
            name="license",
        ),
    ]
