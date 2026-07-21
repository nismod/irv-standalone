from django.db import models

class RasterTileSourceQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_superuser:
            return self

        return self.filter(
            datasets__access_groups__in=user.groups.all()
        ).distinct()


class RasterTileSource(models.Model):
    description = models.CharField(max_length=1024, blank=True, null=True)
    keys = models.JSONField()
    database = models.CharField(max_length=255, default="terracotta.sqlite")

    objects = RasterTileSourceQuerySet.as_manager()

    class Meta:
        db_table = "raster_tile_sources"
