import json
from typing import cast

from map.serializers import (
    ExpectedDamagesDimensionsSerializer,
    AdaptationDimensionsSerializer,
    AdaptationCostBenefitRatioParametersSerializer,
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
