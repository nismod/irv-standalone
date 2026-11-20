from rest_framework import viewsets
from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from map.serializers import (
    FeatureSerializer,
    FeatureDetailSerializer,
    AdaptationCostBenefitSerializer,
    DamagesExpectedSerializer,
    DamagesRpSerializer,
    DatasetSerializer,
    NetworkLayerStyleSerializer,
    RasterLayerSerializer,
    FeatureLayerSerializer,
    with_model_parameters,
)
from map.models import (
    Feature,
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesRp,
    DamagesNpv,
    Dataset,
    NetworkLayerStyle,
    RasterLayer,
    FeatureLayer,
)
from map.permissions import HasDatasetAccess, accessible_feature_layers, inaccessible_hazard_ids


class FeatureViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().filter(layer__in=accessible_feature_layers(self.request.user))
        if self.action == "retrieve":
            restricted = inaccessible_hazard_ids(self.request.user)
            return queryset.prefetch_related(
                Prefetch("adaptationcostbenefit_set", queryset=with_model_parameters(AdaptationCostBenefit.objects.exclude(hazard__in=restricted))),
                Prefetch("damagesexpected_set", queryset=with_model_parameters(DamagesExpected.objects.exclude(hazard__in=restricted))),
                Prefetch("damagesrp_set", queryset=with_model_parameters(DamagesRp.objects.exclude(hazard__in=restricted))),
                Prefetch("damagesnpv_set", queryset=with_model_parameters(DamagesNpv.objects.exclude(hazard__in=restricted))),
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
    lookup_field = "id"

    def get_queryset(self):
        return with_model_parameters(super().get_queryset().filter(
            feature__layer__in=accessible_feature_layers(self.request.user)
        ).exclude(hazard__in=inaccessible_hazard_ids(self.request.user)))


class DamagesExpectedViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DamagesExpected.objects.all()
    serializer_class = DamagesExpectedSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return with_model_parameters(super().get_queryset().filter(
            feature__layer__in=accessible_feature_layers(self.request.user)
        ).exclude(hazard__in=inaccessible_hazard_ids(self.request.user)))


class DamagesRpViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DamagesRp.objects.all()
    serializer_class = DamagesRpSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return with_model_parameters(super().get_queryset().filter(
            feature__layer__in=accessible_feature_layers(self.request.user)
        ).exclude(hazard__in=inaccessible_hazard_ids(self.request.user)))


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


class FeatureLayerViewset(viewsets.ReadOnlyModelViewSet):
    queryset = FeatureLayer.objects.all()
    serializer_class = FeatureLayerSerializer
    permission_classes = [IsAuthenticated, HasDatasetAccess]
    lookup_url_kwarg = "layer_name"

    @extend_schema(parameters=[OpenApiParameter("layer_name", str, OpenApiParameter.PATH)])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return FeatureLayer.objects.select_related("dataset").prefetch_related("dataset__access_groups").order_by("pk")


class RasterLayerViewset(viewsets.ReadOnlyModelViewSet):
    queryset = RasterLayer.objects.all()
    serializer_class = RasterLayerSerializer
    permission_classes = [IsAuthenticated, HasDatasetAccess]
    lookup_url_kwarg = "id"

    @extend_schema(parameters=[OpenApiParameter("id", str, OpenApiParameter.PATH)])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(parameters=[OpenApiParameter("group", str, OpenApiParameter.QUERY, required=False)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = RasterLayer.objects.select_related("dataset", "tile_source").prefetch_related("dataset__access_groups").order_by("pk")
        group = self.request.query_params.get("group")
        return queryset.filter(dataset__group__iexact=group) if group else queryset


class NetworkLayerStyleViewset(viewsets.ReadOnlyModelViewSet):
    queryset = NetworkLayerStyle.objects.all()
    serializer_class = NetworkLayerStyleSerializer
    permission_classes = [IsAuthenticated]
