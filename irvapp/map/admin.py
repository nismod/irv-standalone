from django.contrib import admin
from django import forms
from tree_queries.admin import TreeAdmin

from .models import (
    FeatureLayer,
    Feature,
    InfrastructureNode,
    MapConfig,
    Dataset,
    NetworkLayerStyle,
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
        "color_scheme",
        "color_range",
        "tile_source",
        "stacking_order",
        "display_order",
    ]
    filter_horizontal = ["access_groups"]
    autocomplete_fields = ["tile_source"]
    search_fields = ["id", "label"]


@admin.register(NetworkLayerStyle)
class NetworkLayerStyleAdmin(admin.ModelAdmin):
    list_display = [
        "layer_id",
        "label",
        "style_type",
        "color",
        "min_zoom",
    ]
    list_filter = ["style_type"]
    search_fields = ["layer_id", "label"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "color":
            kwargs["widget"] = forms.TextInput(attrs={"type": "color"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(MapConfig)
class MapConfigAdmin(admin.ModelAdmin):
    list_display = ["config_name", "config_value", "config_type"]


@admin.register(InfrastructureNode)
class InfrastructureNodeAdmin(TreeAdmin):
    list_display = [*TreeAdmin.list_display, "node_name"]
    position_field = "position"  # Enables sibling ordering controls
