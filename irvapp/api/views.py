import json

from django.core.exceptions import FieldError
from django.db.models import ExpressionWrapper, F, FloatField, Sum, Value
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    FeatureSerializer,
    AdaptationCostBenefitSerializer,
    DamagesExpectedSerializer,
    DamagesRpSerializer,
    AttributeLookupRequestSerializer,
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


class AdaptationCostBenefitViewset(viewsets.ModelViewSet):
    queryset = AdaptationCostBenefit.objects.all()
    serializer_class = AdaptationCostBenefitSerializer


class DamagesExpectedViewset(viewsets.ModelViewSet):
    queryset = DamagesExpected.objects.all()
    serializer_class = DamagesExpectedSerializer


class DamagesRpViewset(viewsets.ModelViewSet):
    queryset = DamagesRp.objects.all()
    serializer_class = DamagesRpSerializer


class AttributeLookupView(APIView):
    """Lookup per-feature values for a field group and variable."""

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

    def _parse_parameters(self, field_group, field, parameters_data):
        if field_group == "adaptation" and field == "cost_benefit_ratio":
            serializer = AdaptationCostBenefitRatioParametersSerializer(
                data=parameters_data
            )
            if not serializer.is_valid():
                return None, serializer.errors
            return serializer.validated_data, None
        return None, None

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

        body_serializer = AttributeLookupRequestSerializer(data=request.data)
        if not body_serializer.is_valid():
            return Response(
                body_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        ids = body_serializer.validated_data["ids"]

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
                eael_days = field_params["eael_days"] if field_params else 1
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

        return Response(
            {feature_id: lookup.get(feature_id, None) for feature_id in ids}
        )
