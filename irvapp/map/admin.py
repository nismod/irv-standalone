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
    RasterLayer,
    LayerIdentity,
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
        "dataset",
        "stacking_order",
        "display_order",
    ]
    autocomplete_fields = ["identity"]
    search_fields = ["identity__id"]
    list_select_related = ("identity__dataset",)

    @admin.display(description="Dataset", ordering="identity__dataset__id")
    def dataset(self, layer):
        return layer.identity.dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "label",
        "group",
        "license",
    ]
    filter_horizontal = ["access_groups"]
    search_fields = ["id", "label"]


@admin.register(RasterLayer)
class RasterLayerAdmin(admin.ModelAdmin):
    list_display = ["id", "label", "dataset", "tile_source"]
    autocomplete_fields = ["tile_source", "identity"]
    search_fields = ["identity__id", "label"]
    list_select_related = ("identity__dataset", "tile_source")

    @admin.display(description="Dataset", ordering="identity__dataset__id")
    def dataset(self, layer):
        return layer.identity.dataset


class LayerIdentityForm(forms.ModelForm):
    class Meta:
        model = LayerIdentity
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        identity = self.instance
        if identity.pk and (FeatureLayer.objects.filter(pk=identity.pk).exists() or
                            RasterLayer.objects.filter(pk=identity.pk).exists()):
            kind_field = self.fields.get("kind")
            if kind_field is not None:
                kind_field.disabled = True

    def clean_kind(self):
        kind = self.cleaned_data["kind"]
        if (self.fields["kind"].disabled and "kind" in self.data and
                self.data["kind"] != kind):
            raise forms.ValidationError("Cannot change the type while a layer is attached.")
        return kind


@admin.register(LayerIdentity)
class LayerIdentityAdmin(admin.ModelAdmin):
    form = LayerIdentityForm
    list_display = ["id", "kind", "dataset"]
    search_fields = ["id"]
    autocomplete_fields = ["dataset"]
    list_select_related = ("dataset",)


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
    list_display = [*TreeAdmin.list_display, "node_name", "feature_layer"]
    position_field = "position"  # Enables sibling ordering controls
