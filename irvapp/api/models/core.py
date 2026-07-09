from django.contrib.gis.db import models
from tree_queries.models import OrderableTreeNode, TreeQuerySet


class MapConfig(models.Model):
    config_name = models.CharField(primary_key=True)
    config_value = models.CharField()

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


class Dataset(models.Model):
    id = models.CharField(primary_key=True)
    label = models.CharField()
    group = models.CharField()
    unit = models.CharField()
    stacking_order = models.IntegerField()
    display_order = models.IntegerField()

    class Meta:
        db_table = "datasets"
