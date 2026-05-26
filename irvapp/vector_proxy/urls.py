from django.urls import path

from vector_proxy.views import VectorTileProxyView

urlpatterns = [
    path('', VectorTileProxyView.as_view()),
    path('<path:tile_path>', VectorTileProxyView.as_view()),
]
