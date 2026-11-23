from django.contrib import admin

from .models import RasterTileSource


@admin.register(RasterTileSource)
class RasterTileSourceAdmin(admin.ModelAdmin):
    list_display = ["id", "dataset_list", "keys", "database"]
    search_fields = ["raster_layers__identity__id", "raster_layers__label"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("raster_layers__identity__dataset")

    @admin.display(description="Datasets")
    def dataset_list(self, source):
        return ", ".join(
            layer.identity.dataset.label for layer in source.raster_layers.all()
            if layer.identity.dataset_id is not None
        )
