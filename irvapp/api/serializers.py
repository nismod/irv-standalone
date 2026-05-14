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
