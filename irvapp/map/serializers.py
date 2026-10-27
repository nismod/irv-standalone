from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .permissions import user_has_dataset_access
from .models import (
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesNpv,
    DamagesRp,
    Dataset,
    Feature,
    NetworkLayerStyle,
)


class AdaptationCostBenefitSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField(child=serializers.JSONField()))
    def get_parameters(self, instance):
        return instance.parameter_set.values

    class Meta:
        model = AdaptationCostBenefit
        exclude = ["parameter_set"]


class DamagesExpectedSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField(child=serializers.JSONField()))
    def get_parameters(self, instance):
        return instance.parameter_set.values

    class Meta:
        model = DamagesExpected
        exclude = ["parameter_set"]


class DamagesRpSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField(child=serializers.JSONField()))
    def get_parameters(self, instance):
        return instance.parameter_set.values

    class Meta:
        model = DamagesRp
        exclude = ["parameter_set"]


class DamagesNpvSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField(child=serializers.JSONField()))
    def get_parameters(self, instance):
        return instance.parameter_set.values

    class Meta:
        model = DamagesNpv
        exclude = ["parameter_set"]


class DatasetSerializer(serializers.ModelSerializer):
    has_access = serializers.SerializerMethodField()
    color_range = serializers.ListField(
        child=serializers.FloatField(),
        allow_null=True,
        required=False,
    )

    @extend_schema_field(serializers.BooleanField())
    def get_has_access(self, dataset):
        user = self.context["request"].user
        if not hasattr(self, "_user_group_ids"):
            self._user_group_ids = set(
                user.groups.values_list("pk", flat=True)
            )
        return user_has_dataset_access(
            user,
            dataset,
            user_group_ids=self._user_group_ids,
        )

    class Meta:
        model = Dataset
        fields = [
            "id",
            "label",
            "group",
            "quantity",
            "unit",
            "license",
            "color_scheme",
            "color_range",
            "tile_source",
            "stacking_order",
            "display_order",
            "has_access",
        ]


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'string_id', 'layer', 'sublayer', 'properties']


class NetworkLayerStyleSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="layer_id")
    type = serializers.CharField(source="style_type")
    minZoom = serializers.IntegerField(
        source="min_zoom",
        allow_null=True,
        required=False,
    )

    class Meta:
        model = NetworkLayerStyle
        fields = ["id", "type", "label", "color", "minZoom"]


class FeatureDetailSerializer(serializers.ModelSerializer):
    # Explicitly map to Django's default reverse FK managers.
    adaptation = AdaptationCostBenefitSerializer(
        source='adaptationcostbenefit_set',
        many=True,
        read_only=True,
    )
    damages_expected = DamagesExpectedSerializer(
        source='damagesexpected_set',
        many=True,
        read_only=True,
    )
    damages_return_period = DamagesRpSerializer(
        source='damagesrp_set',
        many=True,
        read_only=True,
    )
    damages_npv = DamagesNpvSerializer(
        source='damagesnpv_set',
        many=True,
        read_only=True,
    )

    class Meta:
        model = Feature
        fields = '__all__'


class AttributeLookupRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


class ExpectedDamagesDimensionsSerializer(serializers.Serializer):
    hazard = serializers.CharField()
    parameters = serializers.DictField(child=serializers.JSONField())
    protection_standard = serializers.IntegerField()


class AdaptationDimensionsSerializer(serializers.Serializer):
    hazard = serializers.CharField()
    parameters = serializers.DictField(child=serializers.JSONField())
    adaptation_name = serializers.CharField()
    adaptation_protection_level = serializers.FloatField()


class AdaptationCostBenefitRatioParametersSerializer(serializers.Serializer):
    eael_days = serializers.IntegerField(min_value=1, max_value=30)

    def validate_eael_days(self, value):
        # Keep parity with FastAPI behavior while upstream data is corrected.
        return value / 15


class ProtectedFeatureSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    string_id = serializers.CharField()
    layer = serializers.CharField()
    adaptation_name = serializers.CharField()
    adaptation_protection_level = serializers.FloatField()
    adaptation_cost = serializers.FloatField(allow_null=True)
    avoided_ead_mean = serializers.FloatField(allow_null=True)
    avoided_eael_mean = serializers.FloatField(allow_null=True)
    hazard = serializers.CharField()
    parameters = serializers.DictField(child=serializers.JSONField())


class SortedFeatureSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    string_id = serializers.CharField()
    layer = serializers.CharField()
    bbox_wkt = serializers.CharField()
    value = serializers.FloatField(allow_null=True)


class AttributeLookupResponseSerializer(serializers.BaseSerializer):
    """Top-level mapping of feature id to value (or null)."""

    def to_representation(self, instance):
        value_field = serializers.FloatField(allow_null=True, required=False)
        return {
            str(feature_id): (
                value_field.to_representation(value)
                if value is not None
                else None
            )
            for feature_id, value in instance.items()
        }
