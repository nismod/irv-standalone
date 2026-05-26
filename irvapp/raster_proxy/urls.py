from django.urls import path

from raster_proxy.views import RasterTileProxyView

urlpatterns = [
    path('', RasterTileProxyView.as_view()),
    path('<path:tile_path>', RasterTileProxyView.as_view()),
]
