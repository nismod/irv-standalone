from django.contrib.gis.db import models

from .core import Feature


class AdaptationCostBenefit(models.Model):
    pk = models.CompositePrimaryKey(
        "feature_id",
        "hazard",
        "rcp",
        "adaptation_name",
        "adaptation_protection_level",
    )
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    rcp = models.CharField(max_length=8)
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
        "feature_id",
        "hazard",
        "rcp",
        "epoch",
        "protection_standard",
    )
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    rcp = models.CharField(max_length=8)
    epoch = models.IntegerField()
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
    pk = models.CompositePrimaryKey("feature_id", "hazard", "rcp")
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    rcp = models.CharField(max_length=8)
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
        "feature_id",
        "hazard",
        "rcp",
        "epoch",
        "rp",
    )
    feature = models.ForeignKey(Feature, models.CASCADE)
    hazard = models.CharField(max_length=8)
    rcp = models.CharField(max_length=8)
    epoch = models.IntegerField()
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
