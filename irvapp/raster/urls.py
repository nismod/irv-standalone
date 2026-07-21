from django.urls import path

from .views import (
    ColormapView,
    RasterTileImageView,
    RasterTileSourceDetailView,
    RasterTileSourceDomainsView,
    RasterTileSourceListView,
)

urlpatterns = [
    path('colormap', ColormapView.as_view()),
    path('sources', RasterTileSourceListView.as_view()),
    path('sources/<int:source_id>', RasterTileSourceDetailView.as_view()),
    path(
        'sources/<slug:dataset_id>/domains',
        RasterTileSourceDomainsView.as_view(),
    ),
    path(
        '<slug:dataset_id>/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
        RasterTileImageView.as_view(),
    ),
]
