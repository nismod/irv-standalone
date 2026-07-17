from django.contrib import admin

from .models import RasterTileSource


@admin.register(RasterTileSource)
class RasterTileSourceAdmin(admin.ModelAdmin):
    list_display = [
        "name", "domain", "group", "dataset", "license", "keys", "database"
    ]
    autocomplete_fields = ["dataset"]
