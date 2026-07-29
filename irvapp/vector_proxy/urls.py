from django.urls import path

from vector_proxy.views import VectorTileProxyView

urlpatterns = [
    path('', VectorTileProxyView.as_view()),
    path('data/<slug:dataset_id>.json', VectorTileProxyView.as_view()),
    path(
        'data/<slug:dataset_id>/<path:tile_path>',
        VectorTileProxyView.as_view(),
    ),
    path('<path:tile_path>', VectorTileProxyView.as_view()),
]
