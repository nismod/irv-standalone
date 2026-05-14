from api.views import (
    FeatureViewset,
    AdaptationCostBenefitViewset,
    DamagesExpectedViewset,
    DamagesRpViewset,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'features', FeatureViewset)
router.register(r'adaptation-cost-benefits', AdaptationCostBenefitViewset)
router.register(r'damages-expected', DamagesExpectedViewset)
router.register(r'damages-rp', DamagesRpViewset)

urlpatterns = router.urls
