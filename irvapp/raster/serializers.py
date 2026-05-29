from rest_framework import serializers

from .models import RasterTileSource


class ColorMapOptionsSerializer(serializers.Serializer):
    """
    Serializer for colormap options
    """

    colormap = serializers.CharField()
    stretch_range = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        allow_null=True,
        min_length=2,
        max_length=2,
    )
    num_values = serializers.IntegerField(default=255)


class ColorMapEntrySerializer(serializers.Serializer):
    """
    Serializer for a single colormap entry (RGB)
    """

    value = serializers.IntegerField(min_value=0, max_value=255)
    rgba = serializers.ListField(
        child=serializers.IntegerField(
            min_value=0,
            max_value=255
        ),
        min_length=4,
        max_length=4,
    )


class ColorMapSerializer(serializers.Serializer):
    """
    Serializer for colormap data
    """

    colormap = serializers.ListField(
        child=ColorMapEntrySerializer()
    )


class RasterTileSourceSerializer(serializers.ModelSerializer):
    # Expose as a typed list so OpenAPI/TS clients don't get `unknown`.
    keys = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = RasterTileSource
        fields = [
            "id",
            "domain",
            "name",
            "group",
            "description",
            "license",
            "keys",
        ]


class RasterTileSourceDomainsSerializer(serializers.Serializer):
    domains = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )
