from django.db import migrations, models


DEFAULT_PATH_TEMPLATE = (
    "{type}__rp_{rp}__rcp_{rcp}__epoch_{epoch}__conf_{confidence}.tif"
)


class Migration(migrations.Migration):

    dependencies = [
        ("raster", "0009_merge_duplicate_raster_tile_sources"),
    ]

    operations = [
        migrations.AddField(
            model_name="rastertilesource",
            name="path_template",
            field=models.CharField(
                default=DEFAULT_PATH_TEMPLATE,
                max_length=1024,
            ),
        ),
    ]
