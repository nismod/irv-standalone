from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from api.serializers import (
    FeatureSerializer,
    FeatureDetailSerializer,
    AdaptationCostBenefitSerializer,
    DamagesExpectedSerializer,
    DamagesRpSerializer,
    DatasetSerializer,
)
from api.models import (
    Feature,
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesRp,
    Dataset,
)


class FeatureViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            return queryset.prefetch_related(
                "adaptationcostbenefit_set",
                "damagesexpected_set",
                "damagesrp_set",
                "damagesnpv_set",
            )
        return queryset

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "retrieve":
            return FeatureDetailSerializer
        return FeatureSerializer


class AdaptationCostBenefitViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AdaptationCostBenefit.objects.all()
    serializer_class = AdaptationCostBenefitSerializer
    permission_classes = [IsAuthenticated]


class DamagesExpectedViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DamagesExpected.objects.all()
    serializer_class = DamagesExpectedSerializer
    permission_classes = [IsAuthenticated]


class DamagesRpViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DamagesRp.objects.all()
    serializer_class = DamagesRpSerializer
    permission_classes = [IsAuthenticated]


class DatasetViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated]
