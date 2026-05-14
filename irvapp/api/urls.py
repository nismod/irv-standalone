from api.views import (
    FeatureViewset,
    AdaptationCostBenefitViewset,
    DamagesExpectedViewset,
    DamagesRpViewset,
    AttributeLookupView,
)
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()
router.register(r'features', FeatureViewset)
router.register(r'adaptation-cost-benefits', AdaptationCostBenefitViewset)
router.register(r'damages-expected', DamagesExpectedViewset)
router.register(r'damages-rp', DamagesRpViewset)

urlpatterns = [
    path('attributes/<str:field_group>/', AttributeLookupView.as_view()),
] + router.urls
