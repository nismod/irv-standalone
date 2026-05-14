from django.contrib import admin

from .models import (
    FeatureLayers,
    Features,
)

# Register your models here.
admin.site.register(Features)
admin.site.register(FeatureLayers)
