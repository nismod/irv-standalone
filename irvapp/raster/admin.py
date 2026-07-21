from django.contrib import admin

from .models import RasterTileSource


@admin.register(RasterTileSource)
class RasterTileSourceAdmin(admin.ModelAdmin):
    list_display = ["id", "dataset_list", "keys", "database"]
    search_fields = ["datasets__id", "datasets__label"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("datasets")

    @admin.display(description="Datasets")
    def dataset_list(self, source):
        return ", ".join(
            dataset.label for dataset in source.datasets.all()
        )
