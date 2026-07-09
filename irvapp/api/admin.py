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
admin.site.register(MapConfig)
admin.site.register(Feature)
admin.site.register(FeatureLayer)
admin.site.register(Dataset)


@admin.register(InfrastructureNode)
class InfrastructureNodeAdmin(TreeAdmin):
    list_display = [*TreeAdmin.list_display, "node_name"]
    position_field = "position"  # Enables sibling ordering controls