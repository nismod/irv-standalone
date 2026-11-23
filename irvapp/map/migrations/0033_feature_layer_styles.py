from django.db import migrations, models
import django.db.models.deletion


def link_existing_styles(apps, schema_editor):
    Style = apps.get_model("map", "FeatureLayerStyle")
    FeatureLayer = apps.get_model("map", "FeatureLayer")
    alias = schema_editor.connection.alias
    layer_ids = FeatureLayer.objects.using(alias).values("pk")
    Style.objects.using(alias).filter(layer_id__in=layer_ids).update(feature_layer_id=models.F("layer_id"))


class Migration(migrations.Migration):
    dependencies = [("map", "0032_remove_featurelayer_dataset_and_more")]

    operations = [
        migrations.RenameModel(old_name="NetworkLayerStyle", new_name="FeatureLayerStyle"),
        migrations.AlterModelTable(name="featurelayerstyle", table="feature_layer_styles"),
        migrations.AddField(
            model_name="featurelayerstyle",
            name="feature_layer",
            field=models.OneToOneField(
                to="map.featurelayer", on_delete=django.db.models.deletion.PROTECT,
                null=True, blank=True, related_name="style",
                help_text="Link the feature layer with the same ID when it exists.",
            ),
        ),
        migrations.RunPython(link_existing_styles, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="featurelayerstyle",
            constraint=models.CheckConstraint(
                condition=models.Q(feature_layer__isnull=True) | models.Q(feature_layer=models.F("layer_id")),
                name="feature_layer_style_matching_id",
            ),
        ),
    ]
