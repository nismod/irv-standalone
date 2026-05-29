from django.urls import path

from .views import ColormapView, RasterTileImageView

urlpatterns = [
    path('colormap', ColormapView.as_view()),
    path(
        '<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
        RasterTileImageView.as_view(),
    ),
]
