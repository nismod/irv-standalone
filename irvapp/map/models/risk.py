import json

from django.contrib.gis.db import models
from django.db.models import BigIntegerField, Func

from .core import Feature


class SequenceNextValue(Func):
    function = "nextval"
    template = "%(function)s('%(sequence_name)s'::regclass)"
    allowed_default = True

    def __init__(self, sequence_name):
        self.sequence_name = sequence_name
        super().__init__(output_field=BigIntegerField(), sequence_name=sequence_name)

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [self.sequence_name],
            {},
        )


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
        prefetched_parameters = getattr(self, "prefetched_parameters", None)
        if prefetched_parameters is None:
            prefetched_parameters = getattr(self, "_prefetched_objects_cache", {}).get(
                "parameters"
            )
        if prefetched_parameters is not None:
            return {
                item.name: item.value
                for item in sorted(prefetched_parameters, key=lambda item: item.name)
            }
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
    pk = models.CompositePrimaryKey(
        "parameter_set_id",
        "feature_id",
        "hazard",
        "adaptation_name",
        "adaptation_protection_level",
    )
    id = models.BigIntegerField(
        editable=False,
        null=True,
        db_default=SequenceNextValue("adaptation_cost_benefit_id_seq"),
    )
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(
        ModelParameterSet, models.PROTECT, db_index=False
    )
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


class DamagesExpected(models.Model):
    pk = models.CompositePrimaryKey(
        "parameter_set_id",
        "feature_id",
        "hazard",
        "protection_standard",
    )
    id = models.BigIntegerField(
        editable=False,
        null=True,
        db_default=SequenceNextValue("damages_expected_id_seq"),
    )
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(
        ModelParameterSet, models.PROTECT, db_index=False
    )
    protection_standard = models.IntegerField()
    ead_amin = models.FloatField(blank=True, null=True)
    ead_mean = models.FloatField(blank=True, null=True)
    ead_amax = models.FloatField(blank=True, null=True)
    eael_amin = models.FloatField(blank=True, null=True)
    eael_mean = models.FloatField(blank=True, null=True)
    eael_amax = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "damages_expected"


class DamagesNpv(models.Model):
    pk = models.CompositePrimaryKey(
        "parameter_set_id",
        "feature_id",
        "hazard",
    )
    id = models.BigIntegerField(
        editable=False,
        null=True,
        db_default=SequenceNextValue("damages_npv_id_seq"),
    )
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(
        ModelParameterSet, models.PROTECT, db_index=False
    )
    ead_amin = models.FloatField(blank=True, null=True)
    ead_mean = models.FloatField(blank=True, null=True)
    ead_amax = models.FloatField(blank=True, null=True)
    eael_amin = models.FloatField(blank=True, null=True)
    eael_mean = models.FloatField(blank=True, null=True)
    eael_amax = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "damages_npv"


class DamagesRp(models.Model):
    pk = models.CompositePrimaryKey(
        "parameter_set_id",
        "feature_id",
        "hazard",
        "rp",
    )
    id = models.BigIntegerField(
        editable=False,
        null=True,
        db_default=SequenceNextValue("damages_rp_id_seq"),
    )
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    parameter_set = models.ForeignKey(
        ModelParameterSet, models.PROTECT, db_index=False
    )
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
