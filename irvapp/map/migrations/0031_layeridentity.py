import django.db.models.deletion
from django.db import migrations, models


def populate_identities(apps, schema_editor):
    FeatureLayer = apps.get_model("map", "FeatureLayer")
    RasterLayer = apps.get_model("map", "RasterLayer")
    Identity = apps.get_model("map", "LayerIdentity")
    alias = schema_editor.connection.alias
    # Block layer writes until the new foreign keys are installed.
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("LOCK TABLE feature_layers, raster_layers IN SHARE ROW EXCLUSIVE MODE")
    feature_ids = set(FeatureLayer.objects.using(alias).values_list("pk", flat=True))
    raster_ids = set(RasterLayer.objects.using(alias).values_list("pk", flat=True))
    collisions = sorted(feature_ids & raster_ids)
    if collisions:
        raise RuntimeError("Feature and raster layer IDs collide: " + ", ".join(collisions))
    Identity.objects.using(alias).bulk_create(
        [Identity(id=value, kind="feature") for value in feature_ids]
        + [Identity(id=value, kind="raster") for value in raster_ids]
    )


def ensure_no_unattached_identities(apps, schema_editor):
    alias = schema_editor.connection.alias
    Identity = apps.get_model("map", "LayerIdentity")
    FeatureLayer = apps.get_model("map", "FeatureLayer")
    RasterLayer = apps.get_model("map", "RasterLayer")
    attached = set(FeatureLayer.objects.using(alias).values_list("pk", flat=True))
    attached.update(RasterLayer.objects.using(alias).values_list("pk", flat=True))
    unattached = list(Identity.objects.using(alias).exclude(pk__in=attached).values_list("pk", flat=True))
    if unattached:
        raise RuntimeError("Cannot reverse while unattached layer identities exist: " + ", ".join(sorted(unattached)))


ADD_FOREIGN_KEYS = """
ALTER TABLE feature_layers ADD CONSTRAINT feature_layer_identity_fk
    FOREIGN KEY (layer_name) REFERENCES layer_identities (id) ON DELETE RESTRICT;
ALTER TABLE raster_layers ADD CONSTRAINT raster_layer_identity_fk
    FOREIGN KEY (id) REFERENCES layer_identities (id) ON DELETE RESTRICT;
ALTER TABLE feature_layers ADD CONSTRAINT feature_layer_identity_kind_fk
    FOREIGN KEY (layer_name, identity_kind) REFERENCES layer_identities (id, kind) ON DELETE RESTRICT;
ALTER TABLE raster_layers ADD CONSTRAINT raster_layer_identity_kind_fk
    FOREIGN KEY (id, identity_kind) REFERENCES layer_identities (id, kind) ON DELETE RESTRICT;
"""

REMOVE_FOREIGN_KEYS = """
ALTER TABLE feature_layers DROP CONSTRAINT feature_layer_identity_kind_fk;
ALTER TABLE raster_layers DROP CONSTRAINT raster_layer_identity_kind_fk;
ALTER TABLE feature_layers DROP CONSTRAINT feature_layer_identity_fk;
ALTER TABLE raster_layers DROP CONSTRAINT raster_layer_identity_fk;
"""


class Migration(migrations.Migration):
    dependencies = [("map", "0030_remove_dataset_quantity_unit")]

    operations = [
        migrations.CreateModel(
            name="LayerIdentity",
            fields=[
                ("id", models.CharField(primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("feature", "Feature"), ("raster", "Raster")], max_length=16)),
            ],
            options={"db_table": "layer_identities"},
        ),
        migrations.RunPython(populate_identities, ensure_no_unattached_identities),
        migrations.AddConstraint(
            model_name="layeridentity",
            constraint=models.UniqueConstraint(fields=("id", "kind"), name="layer_identity_id_kind_unique"),
        ),
        migrations.AddField(
            model_name="featurelayer", name="identity_kind",
            field=models.CharField(db_default="feature", default="feature", editable=False, max_length=16),
        ),
        migrations.AddField(
            model_name="rasterlayer", name="identity_kind",
            field=models.CharField(db_default="raster", default="raster", editable=False, max_length=16),
        ),
        migrations.AddConstraint(
            model_name="featurelayer",
            constraint=models.CheckConstraint(condition=models.Q(identity_kind="feature"), name="feature_layer_identity_kind"),
        ),
        migrations.AddConstraint(
            model_name="rasterlayer",
            constraint=models.CheckConstraint(condition=models.Q(identity_kind="raster"), name="raster_layer_identity_kind"),
        ),
        migrations.RunSQL(ADD_FOREIGN_KEYS, REMOVE_FOREIGN_KEYS),
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.RemoveField(model_name="featurelayer", name="layer_name"),
            migrations.AddField(
                model_name="featurelayer", name="identity",
                field=models.OneToOneField(db_column="layer_name", on_delete=django.db.models.deletion.PROTECT,
                                           primary_key=True, related_name="featurelayer", serialize=False,
                                           to="map.layeridentity"),
            ),
            migrations.RemoveField(model_name="rasterlayer", name="id"),
            migrations.AddField(
                model_name="rasterlayer", name="identity",
                field=models.OneToOneField(db_column="id", on_delete=django.db.models.deletion.PROTECT,
                                           primary_key=True, related_name="rasterlayer", serialize=False,
                                           to="map.layeridentity"),
            ),
        ]),
    ]
