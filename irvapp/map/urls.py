from map.views import (
    MapConfigViewSet,
    InfrastructureTreeViewSet,
    DatasetViewset,
    NetworkLayerStyleViewset,
    RasterLayerViewset,
    FeatureLayerViewset,
)
from rest_framework.routers import DefaultRouter
from django.urls import path
from map.risk.provider import get_risk_provider

risk = get_risk_provider()

router = DefaultRouter(trailing_slash=False)
router.register(r'features', risk.feature_viewset, basename='feature')
router.register(r'adaptation-cost-benefits', risk.adaptation_viewset, basename='adaptationcostbenefit')
router.register(r'damages-expected', risk.expected_damages_viewset, basename='damagesexpected')
router.register(r'damages-rp', risk.return_period_damages_viewset, basename='damagesrp')
router.register(r'datasets', DatasetViewset)
router.register(r'raster-layers', RasterLayerViewset)
router.register(r'feature-layers', FeatureLayerViewset)
router.register(r'network-layer-styles', NetworkLayerStyleViewset)
router.register(r'config', MapConfigViewSet, basename='map-config')
router.register(
    r'infrastructure-tree',
    InfrastructureTreeViewSet,
    basename='infrastructure-tree',
)

urlpatterns = [
    *router.urls,
    path('model-scenarios/<str:field_group>', risk.scenarios_view.as_view()),
    path(
        'features/sorted-by/<str:field_group>',
        risk.sorted_features_view.as_view(),
    ),
    path(
        'features/<int:protector_id>/protected-by',
        risk.protected_features_view.as_view(),
    ),
    path('attributes/<str:field_group>', risk.attribute_lookup_view.as_view()),
]
