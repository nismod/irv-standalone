from django.contrib import admin

from .models import (
    FeatureLayer,
    Feature,
    MapConfig,
)

# Register your models here.
admin.site.register(MapConfig)
admin.site.register(Feature)
admin.site.register(FeatureLayer)
