# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.gis.db import models


class AdaptationCostBenefit(models.Model):
    pk = models.CompositePrimaryKey('feature_id', 'hazard', 'rcp', 'adaptation_name', 'adaptation_protection_level')
    feature = models.ForeignKey('Features', models.DO_NOTHING)
    hazard = models.CharField(max_length=8)
    rcp = models.CharField(max_length=8)
    adaptation_name = models.CharField()
    adaptation_protection_level = models.FloatField()
    adaptation_cost = models.FloatField(blank=True, null=True)
    avoided_ead_amin = models.FloatField(blank=True, null=True)
    avoided_ead_mean = models.FloatField(blank=True, null=True)
    avoided_ead_amax = models.FloatField(blank=True, null=True)
    avoided_eael_amin = models.FloatField(blank=True, null=True)
    avoided_eael_mean = models.FloatField(blank=True, null=True)
    avoided_eael_amax = models.FloatField(blank=True, null=True)
    protector_feature_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adaptation_cost_benefit'


class DamagesExpected(models.Model):
    pk = models.CompositePrimaryKey('feature_id', 'hazard', 'rcp', 'epoch', 'protection_standard')
    feature = models.ForeignKey('Features', models.DO_NOTHING)
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
        managed = False
        db_table = 'damages_expected'


class DamagesNpv(models.Model):
    pk = models.CompositePrimaryKey('feature_id', 'hazard', 'rcp')
    feature = models.ForeignKey('Features', models.DO_NOTHING)
    hazard = models.CharField(max_length=8)
    rcp = models.CharField(max_length=8)
    ead_amin = models.FloatField(blank=True, null=True)
    ead_mean = models.FloatField(blank=True, null=True)
    ead_amax = models.FloatField(blank=True, null=True)
    eael_amin = models.FloatField(blank=True, null=True)
    eael_mean = models.FloatField(blank=True, null=True)
    eael_amax = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'damages_npv'


class DamagesRp(models.Model):
    pk = models.CompositePrimaryKey('feature_id', 'hazard', 'rcp', 'epoch', 'rp')
    feature = models.ForeignKey('Features', models.DO_NOTHING)
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
        managed = False
        db_table = 'damages_rp'


class FeatureLayers(models.Model):
    layer_name = models.CharField(primary_key=True)
    sector = models.CharField()
    subsector = models.CharField()
    asset_type = models.CharField()

    class Meta:
        managed = False
        db_table = 'feature_layers'


class Features(models.Model):
    string_id = models.CharField()
    layer = models.ForeignKey(FeatureLayers, models.DO_NOTHING, db_column='layer')
    sublayer = models.CharField(blank=True, null=True)
    properties = models.TextField()  # This field type is a guess.
    geom = models.GeometryField()

    class Meta:
        managed = False
        db_table = 'features'
