from django.contrib import admin
from tree_queries.admin import TreeAdmin

from .models import (
    FeatureLayer,
    Feature,
    InfrastructureNode,
    MapConfig,
    Dataset
)


# Register your models here.
@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = [
        "string_id",
        "layer",
        "sublayer",
    ]
    list_select_related = ("layer",)


@admin.register(FeatureLayer)
class FeatureLayerAdmin(admin.ModelAdmin):
    list_display = [
        "layer_name",
        "sector",
        "subsector",
        "asset_type",
    ]


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "label",
        "group",
        "quantity",
        "unit",
        "license",
        "tile_source",
        "stacking_order",
        "display_order",
    ]
    filter_horizontal = ["access_groups"]
    autocomplete_fields = ["tile_source"]
    search_fields = ["id", "label"]


@admin.register(MapConfig)
class MapConfigAdmin(admin.ModelAdmin):
    list_display = ["config_name", "config_value", "config_type"]


@admin.register(InfrastructureNode)
class InfrastructureNodeAdmin(TreeAdmin):
    list_display = [*TreeAdmin.list_display, "node_name"]
    position_field = "position"  # Enables sibling ordering controls
