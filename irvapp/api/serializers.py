from rest_framework import serializers
from .models import Feature, AdaptationCostBenefit, DamagesExpected, DamagesRp


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = '__all__'


class AdaptationCostBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptationCostBenefit
        fields = '__all__'


class DamagesExpectedSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamagesExpected
        fields = '__all__'


class DamagesRpSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamagesRp
        fields = '__all__'


class AttributeLookupRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


class ExpectedDamagesDimensionsSerializer(serializers.Serializer):
    hazard = serializers.CharField()
    rcp = serializers.CharField()
    epoch = serializers.IntegerField()
    protection_standard = serializers.IntegerField()


class AdaptationDimensionsSerializer(serializers.Serializer):
    hazard = serializers.CharField()
    rcp = serializers.CharField()
    adaptation_name = serializers.CharField()
    adaptation_protection_level = serializers.FloatField()


class AdaptationCostBenefitRatioParametersSerializer(serializers.Serializer):
    eael_days = serializers.IntegerField(min_value=1, max_value=30)

    def validate_eael_days(self, value):
        # Keep parity with FastAPI behavior while upstream data is corrected.
        return value / 15
