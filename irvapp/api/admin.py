from django.contrib import admin

from .models import (
    FeatureLayer,
    Feature,
)

# Register your models here.
admin.site.register(Feature)
admin.site.register(FeatureLayer)
