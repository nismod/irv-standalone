from django.urls import path

from .views import ColormapView, RasterTileProxyView

urlpatterns = [
    path('', RasterTileProxyView.as_view()),
    path('colormap', ColormapView.as_view()),
    path('<path:tile_path>', RasterTileProxyView.as_view()),
]
