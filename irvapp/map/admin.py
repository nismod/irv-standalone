from django.contrib import admin
from django import forms
from django.db import router
from tree_queries.admin import TreeAdmin

from .models import (
    FeatureLayer,
    Feature,
    InfrastructureNode,
    MapConfig,
    Dataset,
    FeatureLayerStyle,
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


class DatasetChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, dataset):
        return dataset.label


class LayerDatasetForm(forms.ModelForm):
    dataset = DatasetChoiceField(queryset=Dataset.objects.order_by("label", "pk"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "dataset" in self.fields and self.instance.pk and not self.instance._state.adding:
            self.initial["dataset"] = self.instance.identity.dataset_id


class LayerDatasetAdminMixin:
    form = LayerDatasetForm

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        fields.remove("dataset")
        fields.insert(fields.index("identity"), "dataset")
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        identity_admin = self.admin_site._registry[LayerIdentity]
        dataset_admin = self.admin_site._registry[Dataset]
        identity = obj.identity if obj is not None else None
        if not identity_admin.has_change_permission(request, identity) or not dataset_admin.has_view_permission(request):
            return (*readonly, "dataset")
        return readonly

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if "dataset" not in form.cleaned_data:
            return
        dataset = form.cleaned_data["dataset"]
        if (change and "dataset" not in form.changed_data) or (not change and dataset is None):
            return
        alias = router.db_for_write(LayerIdentity, instance=obj.identity)
        identity = LayerIdentity.objects.using(alias).select_for_update().get(pk=obj.pk)
        identity.dataset = dataset
        identity.save(using=alias, update_fields=["dataset"])


@admin.register(FeatureLayer)
class FeatureLayerAdmin(LayerDatasetAdminMixin, admin.ModelAdmin):
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
class RasterLayerAdmin(LayerDatasetAdminMixin, admin.ModelAdmin):
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


@admin.register(FeatureLayerStyle)
class FeatureLayerStyleAdmin(admin.ModelAdmin):
    list_display = [
        "layer_id",
        "feature_layer",
        "label",
        "style_type",
        "color",
        "min_zoom",
    ]
    list_filter = ["style_type"]
    search_fields = ["layer_id", "label"]
    autocomplete_fields = ["feature_layer"]
    list_select_related = ("feature_layer",)

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
