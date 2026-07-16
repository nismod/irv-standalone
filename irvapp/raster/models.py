from django.db import models


class RasterTileSource(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255)
    description = models.CharField(max_length=1024, blank=True, null=True)
    license = models.CharField(max_length=255, blank=True, null=True)
    keys = models.JSONField()
    database = models.CharField(max_length=255, default="terracotta.sqlite")

    class Meta:
        db_table = "raster_tile_sources"
