from django.db import models

from api.models import Dataset


class RasterTileSourceQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_superuser:
            return self

        visible_datasets = Dataset.objects.visible_to(user)
        return self.filter(dataset__in=visible_datasets).distinct()


class RasterTileSource(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255)
    description = models.CharField(max_length=1024, blank=True, null=True)
    keys = models.JSONField()
    database = models.CharField(max_length=255, default="terracotta.sqlite")
    dataset = models.ForeignKey(
        "api.Dataset",
        models.PROTECT,
        blank=True,
        null=True,
        related_name="raster_tile_sources",
    )

    objects = RasterTileSourceQuerySet.as_manager()

    class Meta:
        db_table = "raster_tile_sources"
