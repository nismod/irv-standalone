from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

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
from api.permissions import HasDatasetAccess


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
    permission_classes = [IsAuthenticated, HasDatasetAccess]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Optional dataset group filter "
                    "(for example, hazards)."
                ),
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: DatasetSerializer,
            403: OpenApiResponse(description="Dataset access denied."),
            404: OpenApiResponse(description="Dataset not found."),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Dataset.objects.all()
        if self.action == "list":
            queryset = queryset.prefetch_related("access_groups")
        group = self.request.query_params.get("group")
        if group:
            queryset = queryset.filter(group__iexact=group)
        return queryset
