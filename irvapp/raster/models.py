from django.db import models

DEFAULT_PATH_TEMPLATE = (
    "{type}__rp_{rp}__rcp_{rcp}__epoch_{epoch}__conf_{confidence}.tif"
)


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
    path_template = models.CharField(
        max_length=1024,
        default=DEFAULT_PATH_TEMPLATE,
    )

    objects = RasterTileSourceQuerySet.as_manager()

    class Meta:
        db_table = "raster_tile_sources"
