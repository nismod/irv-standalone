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
admin.site.register(Feature)
admin.site.register(FeatureLayer)
admin.site.register(Dataset)


@admin.register(MapConfig)
class MapConfigAdmin(admin.ModelAdmin):
    list_display = ["config_name", "config_value", "config_type"]


@admin.register(InfrastructureNode)
class InfrastructureNodeAdmin(TreeAdmin):
    list_display = [*TreeAdmin.list_display, "node_name"]
    position_field = "position"  # Enables sibling ordering controls
