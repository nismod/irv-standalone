from map.views import (
    FeatureViewset,
    AdaptationCostBenefitViewset,
    DamagesExpectedViewset,
    DamagesRpViewset,
    AttributeLookupView,
    ProtectedFeaturesView,
    SortedFeaturesView,
    MapConfigViewSet,
    InfrastructureTreeViewSet,
    DatasetViewset,
    NetworkLayerStyleViewset,
    RasterLayerViewset,
    FeatureLayerViewset,
)
from rest_framework.routers import DefaultRouter
from django.urls import path
from map.views.model_scenarios import ModelScenariosView

router = DefaultRouter(trailing_slash=False)
router.register(r'features', FeatureViewset)
router.register(r'adaptation-cost-benefits', AdaptationCostBenefitViewset)
router.register(r'damages-expected', DamagesExpectedViewset)
router.register(r'damages-rp', DamagesRpViewset)
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
    path('model-scenarios/<str:field_group>', ModelScenariosView.as_view()),
    path(
        'features/sorted-by/<str:field_group>',
        SortedFeaturesView.as_view(),
    ),
    path(
        'features/<int:protector_id>/protected-by',
        ProtectedFeaturesView.as_view(),
    ),
    path('attributes/<str:field_group>', AttributeLookupView.as_view()),
]
