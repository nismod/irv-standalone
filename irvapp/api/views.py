import json
from typing import cast

from django.core.exceptions import FieldError
from django.contrib.gis.db.models.functions import AsWKT, Envelope
from django.db.models import ExpressionWrapper, F, FloatField, Sum, Value
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, viewsets, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    FeatureSerializer,
    FeatureDetailSerializer,
    SortedFeatureSerializer,
    AdaptationCostBenefitSerializer,
    DamagesExpectedSerializer,
    DamagesRpSerializer,
    ProtectedFeatureSerializer,
    AttributeLookupRequestSerializer,
    AttributeLookupResponseSerializer,
    ExpectedDamagesDimensionsSerializer,
    AdaptationDimensionsSerializer,
    AdaptationCostBenefitRatioParametersSerializer,
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


class AdaptationCostBenefitViewset(viewsets.ModelViewSet):
    queryset = AdaptationCostBenefit.objects.all()
    serializer_class = AdaptationCostBenefitSerializer


class DamagesExpectedViewset(viewsets.ModelViewSet):
    queryset = DamagesExpected.objects.all()
    serializer_class = DamagesExpectedSerializer


class DamagesRpViewset(viewsets.ModelViewSet):
    queryset = DamagesRp.objects.all()
    serializer_class = DamagesRpSerializer


class FastAPIPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "size"
    page_size = 50

    def get_paginated_response(self, data):
        page_size = (
            self.get_page_size(self.request)
            or self.page.paginator.per_page
        )
        return Response(
            {
                "items": data,
                "total": self.page.paginator.count,
                "page": self.page.number,
                "size": page_size,
                "pages": self.page.paginator.num_pages,
            }
        )


class FieldGroupQueryParsingMixin:

    def _parse_json_query_param(self, request, key):
        raw = request.query_params.get(key)
        if raw is None:
            return None, {key: ["This query parameter is required."]}
        try:
            return json.loads(raw), None
        except json.JSONDecodeError:
            return None, {key: ["Must be valid JSON."]}

    def _parse_dimensions(self, field_group, dimensions_data):
        serializers_by_group = {
            "damages_expected": ExpectedDamagesDimensionsSerializer,
            "adaptation": AdaptationDimensionsSerializer,
        }
        dimensions_serializer_class = serializers_by_group.get(field_group)
        if dimensions_serializer_class is None:
            return None, {"field_group": ["Invalid field group."]}

        serializer = dimensions_serializer_class(data=dimensions_data)
        if not serializer.is_valid():
            return None, serializer.errors
        return serializer.validated_data, None

    def _parse_parameters(
        self,
        field_group,
        field,
        parameters_data,
    ) -> tuple[dict[str, float] | None, object | None]:
        if field_group == "adaptation" and field == "cost_benefit_ratio":
            serializer = AdaptationCostBenefitRatioParametersSerializer(
                data=parameters_data
            )
            if not serializer.is_valid():
                return None, serializer.errors
            return cast(dict[str, float], serializer.validated_data), None
        return None, None


class SortedFeaturesView(FieldGroupQueryParsingMixin, APIView):
    """Return features sorted by a requested attribute value."""

    pagination_class = FastAPIPagination
    serializer_class = SortedFeatureSerializer

    def _layer_filters(self, request):
        filters = {}
        query_fields = {
            "layer": "feature__layer__layer_name",
            "sector": "feature__layer__sector",
            "subsector": "feature__layer__subsector",
            "asset_type": "feature__layer__asset_type",
        }
        for query_param, model_field in query_fields.items():
            value = request.query_params.get(query_param)
            if value is not None:
                filters[model_field] = value
        return filters

    def _serialize_rows(self, rows):
        return [
            {
                "id": row["feature_id"],
                "string_id": row["feature__string_id"],
                "layer": row["feature__layer__layer_name"],
                "bbox_wkt": row["bbox_wkt"],
                "value": row["value"],
            }
            for row in rows
        ]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "field",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Field name to sort by",
            ),
            OpenApiParameter(
                "dimensions",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="JSON object with dimension filters",
            ),
            OpenApiParameter(
                "parameters",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="JSON object with field parameters",
            ),
            OpenApiParameter(
                "page",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
                description="Page number (default 1)",
            ),
            OpenApiParameter(
                "size",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
                description="Page size (default 50)",
            ),
            OpenApiParameter(
                "layer",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="Filter by layer",
            ),
            OpenApiParameter(
                "sector",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="Filter by sector",
            ),
            OpenApiParameter(
                "subsector",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="Filter by subsector",
            ),
            OpenApiParameter(
                "asset_type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="Filter by asset type",
            ),
        ],
        responses=inline_serializer(
            'PaginatedSortedFeatureListResponse',
            {
                'items': SortedFeatureSerializer(many=True),
                'total': serializers.IntegerField(),
                'page': serializers.IntegerField(),
                'size': serializers.IntegerField(),
                'pages': serializers.IntegerField(),
            }
        ),
    )
    def get(self, request, field_group):
        field = request.query_params.get("field")
        if not field:
            return Response(
                {"field": ["This query parameter is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dimensions_data, dimensions_parse_error = self._parse_json_query_param(
            request, "dimensions"
        )
        if dimensions_parse_error is not None:
            return Response(
                dimensions_parse_error,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.query_params.get("parameters") is None:
            parameters_data = {}
        else:
            parameters_data, parameters_parse_error = (
                self._parse_json_query_param(request, "parameters")
            )
            if parameters_parse_error is not None:
                return Response(
                    parameters_parse_error,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        dimensions, dimensions_error = self._parse_dimensions(
            field_group, dimensions_data
        )
        if dimensions_error is not None:
            return Response(
                dimensions_error,
                status=status.HTTP_400_BAD_REQUEST,
            )
        if dimensions is None:
            return Response(
                {"dimensions": ["Invalid dimensions payload."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        field_params, field_params_error = self._parse_parameters(
            field_group, field, parameters_data
        )
        if field_params_error is not None:
            return Response(
                field_params_error,
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_filters = self._layer_filters(request)

        try:
            if field_group == "damages_expected":
                query = DamagesExpected.objects.filter(
                    **base_filters,
                    rcp=dimensions["rcp"],
                    epoch=dimensions["epoch"],
                    protection_standard=dimensions["protection_standard"],
                ).annotate(
                    bbox_wkt=AsWKT(Envelope("feature__geom")),
                )
                if dimensions["hazard"] != "all":
                    query = query.filter(hazard=dimensions["hazard"])
                    query = query.annotate(value=F(field))
                else:
                    query = query.values(
                        "feature_id",
                        "feature__string_id",
                        "feature__layer__layer_name",
                        "bbox_wkt",
                    ).annotate(value=Sum(field))
            elif field_group == "adaptation":
                query = AdaptationCostBenefit.objects.filter(
                    **base_filters,
                    hazard=dimensions["hazard"],
                    rcp=dimensions["rcp"],
                    adaptation_name=dimensions["adaptation_name"],
                    adaptation_protection_level=dimensions[
                        "adaptation_protection_level"
                    ],
                ).annotate(
                    bbox_wkt=AsWKT(Envelope("feature__geom")),
                )

                if field == "cost_benefit_ratio":
                    eael_days = 1
                    if field_params is not None:
                        eael_days = field_params["eael_days"]
                    query = query.annotate(
                        value=ExpressionWrapper(
                            (
                                F("avoided_ead_mean")
                                + F("avoided_eael_mean") * Value(eael_days)
                            )
                            / F("adaptation_cost"),
                            output_field=FloatField(),
                        )
                    )
                else:
                    query = query.annotate(value=F(field))
            else:
                return Response(
                    {"field_group": ["Invalid field group."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except FieldError:
            return Response(
                {"field": ["Invalid field for the requested field group."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if field_group == "damages_expected" and dimensions["hazard"] != "all":
            query = query.values(
                "feature_id",
                "feature__string_id",
                "feature__layer__layer_name",
                "bbox_wkt",
                "value",
            )
        elif field_group == "adaptation":
            query = query.values(
                "feature_id",
                "feature__string_id",
                "feature__layer__layer_name",
                "bbox_wkt",
                "value",
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            query.order_by("-value"), request, view=self
        )
        rows = self._serialize_rows(page)
        serializer = self.serializer_class(rows, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProtectedFeaturesView(APIView):
    """Return adaptation options protected by a given feature."""

    serializer_class = ProtectedFeatureSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "rcp",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description=(
                    "RCP (Representative Concentration Pathway) value"
                ),
            ),
        ],
        responses=ProtectedFeatureSerializer(many=True),
    )
    def get(self, request, protector_id):
        rcp = request.query_params.get("rcp")
        if not rcp:
            return Response(
                {"rcp": ["This query parameter is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = (
            AdaptationCostBenefit.objects.filter(
                protector_feature_id=protector_id,
                rcp=rcp,
            )
            .values(
                "feature_id",
                "feature__string_id",
                "feature__layer__layer_name",
                "adaptation_name",
                "adaptation_protection_level",
                "adaptation_cost",
                "avoided_ead_mean",
                "avoided_eael_mean",
                "hazard",
                "rcp",
            )
            .order_by("feature_id", "adaptation_name", "hazard", "rcp")
        )

        rows = [
            {
                "id": row["feature_id"],
                "string_id": row["feature__string_id"],
                "layer": row["feature__layer__layer_name"],
                "adaptation_name": row["adaptation_name"],
                "adaptation_protection_level": row[
                    "adaptation_protection_level"
                ],
                "adaptation_cost": row["adaptation_cost"],
                "avoided_ead_mean": row["avoided_ead_mean"],
                "avoided_eael_mean": row["avoided_eael_mean"],
                "hazard": row["hazard"],
                "rcp": row["rcp"],
            }
            for row in query
        ]
        serializer = self.serializer_class(rows, many=True)
        return Response(serializer.data)


class AttributeLookupView(FieldGroupQueryParsingMixin, APIView):
    """Lookup per-feature values for a field group and variable."""

    serializer_class = AttributeLookupResponseSerializer

    @extend_schema(
        request=AttributeLookupRequestSerializer,
        parameters=[
            OpenApiParameter(
                "layer",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Asset layer ID",
            ),
            OpenApiParameter(
                "field",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Field name to look up",
            ),
            OpenApiParameter(
                "dimensions",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="JSON object with dimension filters",
            ),
            OpenApiParameter(
                "parameters",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="JSON object with field parameters",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "additionalProperties": {
                        "type": "number",
                        "format": "double",
                        "nullable": True,
                    },
                }
            )
        },
    )
    def post(self, request, field_group):
        layer = request.query_params.get("layer")
        field = request.query_params.get("field")

        if not layer or not field:
            return Response(
                {
                    "detail": (
                        "Both 'layer' and 'field' query parameters "
                        "are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_body = request.data
        if isinstance(request_body, list):
            request_body = {"ids": request_body}

        body_serializer = AttributeLookupRequestSerializer(data=request_body)
        if not body_serializer.is_valid():
            return Response(
                body_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        validated_data = cast(
            dict[str, list[int]],
            body_serializer.validated_data,
        )
        ids = validated_data["ids"]

        dimensions_data, dimensions_parse_error = self._parse_json_query_param(
            request, "dimensions"
        )
        if dimensions_parse_error is not None:
            return Response(
                dimensions_parse_error,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.query_params.get("parameters") is None:
            parameters_data = {}
        else:
            parameters_data, parameters_parse_error = (
                self._parse_json_query_param(request, "parameters")
            )
            if parameters_parse_error is not None:
                return Response(
                    parameters_parse_error,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        dimensions, dimensions_error = self._parse_dimensions(
            field_group, dimensions_data
        )
        if dimensions_error is not None:
            return Response(
                dimensions_error,
                status=status.HTTP_400_BAD_REQUEST,
            )
        if dimensions is None:
            return Response(
                {"dimensions": ["Invalid dimensions payload."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        field_params, field_params_error = self._parse_parameters(
            field_group, field, parameters_data
        )
        if field_params_error is not None:
            return Response(
                field_params_error,
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_feature_ids = Feature.objects.filter(
            layer_id=layer,
            id__in=ids,
        ).values_list("id", flat=True)

        lookup = {}

        if field_group == "damages_expected":
            query = DamagesExpected.objects.filter(
                feature_id__in=base_feature_ids,
                rcp=dimensions["rcp"],
                epoch=dimensions["epoch"],
                protection_standard=dimensions["protection_standard"],
            )

            if dimensions["hazard"] != "all":
                query = query.filter(hazard=dimensions["hazard"])
                try:
                    lookup = dict(query.values_list("feature_id", field))
                except FieldError:
                    return Response(
                        {"field": ["Invalid field for damages_expected."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                try:
                    value_rows = query.values("feature_id").annotate(
                        value=Sum(field)
                    )
                except FieldError:
                    return Response(
                        {"field": ["Invalid field for damages_expected."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                lookup = {
                    row["feature_id"]: row["value"]
                    for row in value_rows
                }

        elif field_group == "adaptation":
            query = AdaptationCostBenefit.objects.filter(
                feature_id__in=base_feature_ids,
                hazard=dimensions["hazard"],
                rcp=dimensions["rcp"],
                adaptation_name=dimensions["adaptation_name"],
                adaptation_protection_level=dimensions[
                    "adaptation_protection_level"
                ],
            )

            if field == "cost_benefit_ratio":
                eael_days = 1
                if field_params is not None:
                    eael_days = field_params["eael_days"]
                ratio = ExpressionWrapper(
                    (
                        F("avoided_ead_mean")
                        + F("avoided_eael_mean") * Value(eael_days)
                    )
                    / F("adaptation_cost"),
                    output_field=FloatField(),
                )
                value_rows = query.annotate(value=ratio).values_list(
                    "feature_id", "value"
                )
                lookup = dict(value_rows)
            else:
                try:
                    lookup = dict(query.values_list("feature_id", field))
                except FieldError:
                    return Response(
                        {"field": ["Invalid field for adaptation."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        else:
            return Response(
                {"field_group": ["Invalid field group."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = {
            feature_id: lookup.get(feature_id, None) for feature_id in ids
        }
        serializer = self.serializer_class(response_data)
        return Response(serializer.data)
