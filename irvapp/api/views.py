from rest_framework import viewsets

from api.serializers import (
    FeatureSerializer,
    AdaptationCostBenefitSerializer,
    DamagesExpectedSerializer,
    DamagesRpSerializer,
)
from api.models import (
    Feature,
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesRp,
)


class FeatureViewset(viewsets.ModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer


class AdaptationCostBenefitViewset(viewsets.ModelViewSet):
    queryset = AdaptationCostBenefit.objects.all()
    serializer_class = AdaptationCostBenefitSerializer


class DamagesExpectedViewset(viewsets.ModelViewSet):
    queryset = DamagesExpected.objects.all()
    serializer_class = DamagesExpectedSerializer


class DamagesRpViewset(viewsets.ModelViewSet):
    queryset = DamagesRp.objects.all()
    serializer_class = DamagesRpSerializer