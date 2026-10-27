import json

from django.contrib.gis.db import models

from .core import Feature


class ModelParameterSet(models.Model):
    """Reusable set of named values that define a model scenario."""

    model_type = models.CharField(max_length=32)
    canonical_key = models.TextField()

    class Meta:
        db_table = "model_parameter_set"
        constraints = [
            models.UniqueConstraint(
                fields=["model_type", "canonical_key"],
                name="unique_model_parameter_set",
            ),
        ]

    @classmethod
    def for_values(cls, model_type, values):
        canonical_key = json.dumps(
            values, sort_keys=True, separators=(",", ":")
        )
        parameter_set, _ = cls.objects.get_or_create(
            model_type=model_type, canonical_key=canonical_key
        )
        for name, value in values.items():
            ModelParameter.objects.get_or_create(
                parameter_set=parameter_set,
                name=name,
                defaults={"value": value},
            )
        return parameter_set

    @property
    def values(self):
        return {
            item.name: item.value
            for item in self.parameters.order_by("name")
        }


class ModelParameter(models.Model):
    parameter_set = models.ForeignKey(
        ModelParameterSet, models.CASCADE, related_name="parameters"
    )
    name = models.CharField(max_length=64)
    value = models.JSONField()

    class Meta:
        db_table = "model_parameter"
        constraints = [
            models.UniqueConstraint(
                fields=["parameter_set", "name"],
                name="unique_parameter_name_per_set",
            ),
        ]


class AdaptationCostBenefit(models.Model):
    id = models.BigAutoField(primary_key=True)
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(ModelParameterSet, models.PROTECT)
    adaptation_name = models.CharField()
    adaptation_protection_level = models.FloatField()
    protector_feature_id = models.IntegerField(blank=True, null=True)
    adaptation_cost = models.FloatField(blank=True, null=True)
    avoided_ead_amin = models.FloatField(blank=True, null=True)
    avoided_ead_mean = models.FloatField(blank=True, null=True)
    avoided_ead_amax = models.FloatField(blank=True, null=True)
    avoided_eael_amin = models.FloatField(blank=True, null=True)
    avoided_eael_mean = models.FloatField(blank=True, null=True)
    avoided_eael_amax = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "adaptation_cost_benefit"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "feature",
                    "hazard",
                    "parameter_set",
                    "adaptation_name",
                    "adaptation_protection_level",
                ],
                name="unique_adaptation_result",
            ),
        ]


class DamagesExpected(models.Model):
    id = models.BigAutoField(primary_key=True)
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(ModelParameterSet, models.PROTECT)
    protection_standard = models.IntegerField()
    ead_amin = models.FloatField(blank=True, null=True)
    ead_mean = models.FloatField(blank=True, null=True)
    ead_amax = models.FloatField(blank=True, null=True)
    eael_amin = models.FloatField(blank=True, null=True)
    eael_mean = models.FloatField(blank=True, null=True)
    eael_amax = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "damages_expected"
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "hazard", "parameter_set", "protection_standard"],
                name="unique_expected_damage_result",
            ),
        ]


class DamagesNpv(models.Model):
    id = models.BigAutoField(primary_key=True)
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(ModelParameterSet, models.PROTECT)
    ead_amin = models.FloatField(blank=True, null=True)
    ead_mean = models.FloatField(blank=True, null=True)
    ead_amax = models.FloatField(blank=True, null=True)
    eael_amin = models.FloatField(blank=True, null=True)
    eael_mean = models.FloatField(blank=True, null=True)
    eael_amax = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "damages_npv"
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "hazard", "parameter_set"],
                name="unique_npv_damage_result",
            ),
        ]


class DamagesRp(models.Model):
    id = models.BigAutoField(primary_key=True)
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(ModelParameterSet, models.PROTECT)
    rp = models.IntegerField()
    exposure = models.FloatField(blank=True, null=True)
    damage_amin = models.FloatField(blank=True, null=True)
    damage_mean = models.FloatField(blank=True, null=True)
    damage_amax = models.FloatField(blank=True, null=True)
    loss_amin = models.FloatField(blank=True, null=True)
    loss_mean = models.FloatField(blank=True, null=True)
    loss_amax = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "damages_rp"
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "hazard", "parameter_set", "rp"],
                name="unique_return_period_damage_result",
            ),
        ]
