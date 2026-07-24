from django.contrib.gis.db import models
from tree_queries.models import OrderableTreeNode, TreeQuerySet


class MapConfig(models.Model):
    config_name = models.CharField(primary_key=True)
    config_value = models.CharField()
    config_type = models.CharField(
        choices=[
            ("number", "Number"),
            ("string", "String"),
            ("boolean", "Boolean"),
        ],
        default='number'
    )

    class Meta:
        db_table = "map_config"


class InfrastructureNode(OrderableTreeNode):
    node_id = models.CharField(primary_key=True)
    node_name = models.CharField()
    objects = TreeQuerySet.as_manager(with_tree_fields=True)

    class Meta(OrderableTreeNode.Meta):
        db_table = "infrastructure_nodes"


class FeatureLayer(models.Model):
    layer_name = models.CharField(primary_key=True)
    sector = models.CharField()
    subsector = models.CharField()
    asset_type = models.CharField()

    class Meta:
        db_table = "feature_layers"


class Feature(models.Model):
    string_id = models.CharField()
    layer = models.ForeignKey(
        FeatureLayer,
        models.CASCADE,
        db_column="layer",
    )
    sublayer = models.CharField(blank=True, null=True)
    properties = models.JSONField()
    geom = models.GeometryField()

    class Meta:
        db_table = "features"


class DatasetQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_superuser:
            return self

        return self.filter(
            access_groups__in=user.groups.all()
        ).distinct()


class Dataset(models.Model):
    id = models.CharField(primary_key=True)
    label = models.CharField()
    group = models.CharField()
    quantity = models.CharField()
    unit = models.CharField()
    license = models.CharField(max_length=255, blank=True, null=True)
    color_scheme = models.CharField(max_length=255, blank=True, null=True)
    color_range = models.JSONField(blank=True, null=True)
    tile_source = models.ForeignKey(
        "raster.RasterTileSource",
        models.PROTECT,
        blank=True,
        null=True,
        related_name="datasets",
    )
    stacking_order = models.IntegerField()
    display_order = models.IntegerField()
    access_groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="datasets",
    )

    objects = DatasetQuerySet.as_manager()

    class Meta:
        db_table = "datasets"
