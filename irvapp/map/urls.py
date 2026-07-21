from map.views import (
    FeatureViewset,
    AdaptationCostBenefitViewset,
    DamagesExpectedViewset,
    DamagesRpViewset,
    AttributeLookupView,
    ProtectedFeaturesView,
    SortedFeaturesView,
    MapConfigViewSet,
    InfrastructureNodeViewSet,
    DatasetViewset,
)
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter(trailing_slash=False)
router.register(r'features', FeatureViewset)
router.register(r'adaptation-cost-benefits', AdaptationCostBenefitViewset)
router.register(r'damages-expected', DamagesExpectedViewset)
router.register(r'damages-rp', DamagesRpViewset)
router.register(r'datasets', DatasetViewset)
router.register(r'config', MapConfigViewSet, basename='map-config')
router.register(
    r'infrastructure-tree',
    InfrastructureNodeViewSet,
    basename='infrastructure-tree',
)

urlpatterns = [
    *router.urls,
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
