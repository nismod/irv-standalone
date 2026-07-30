import math
import numbers
from typing import Any, cast

from rest_framework import serializers


class PixelDataSerializer(serializers.Serializer):
    """Serialize point_query payload: column names to value lists."""

    key = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    hazard = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    rp = serializers.ListField(
        child=serializers.FloatField(allow_null=True),
        required=False,
    )
    rcp = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
    )
    epoch = serializers.ListField(
        child=serializers.FloatField(allow_null=True),
        required=False,
    )
    confidence = serializers.ListField(
        child=serializers.FloatField(allow_null=True),
        required=False,
    )
    variable = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    unit = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
    )
    band_data = serializers.ListField(
        child=serializers.FloatField(allow_null=True),
        required=False,
    )

    def to_representation(self, instance) -> dict[str, Any]:
        if not instance:
            return {}

        # Pixel layer dimensions are defined by the layer metadata CSV and
        # may vary between datasets.  Do not filter the payload through the
        # fixed fields declared above; those fields remain useful for schema
        # documentation and existing clients, while arbitrary dimensions
        # must pass through unchanged.
        sanitized = self._replace_non_finite(dict(instance))
        return cast(dict[str, Any], sanitized)

    def _replace_non_finite(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._replace_non_finite(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [self._replace_non_finite(item) for item in value]

        if isinstance(value, numbers.Real) and not isinstance(value, bool):
            as_float = float(value)
            if not math.isfinite(as_float):
                return None

        return value
