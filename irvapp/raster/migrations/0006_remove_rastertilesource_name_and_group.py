from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("raster", "0005_remove_rastertilesource_license"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rastertilesource",
            name="name",
        ),
        migrations.RemoveField(
            model_name="rastertilesource",
            name="group",
        ),
    ]
