import warnings

import django.db.models.deletion
from django.db import migrations, models


def link_matching_leaves(apps, schema_editor):
    Node = apps.get_model("map", "InfrastructureNode")
    Layer = apps.get_model("map", "FeatureLayer")
    alias = schema_editor.connection.alias
    nodes = Node.objects.using(alias)
    layer_ids = set(Layer.objects.using(alias).values_list("pk", flat=True))
    missing = []
    for node in nodes.filter(children__isnull=True).iterator():
        if node.pk in layer_ids:
            nodes.filter(pk=node.pk).update(feature_layer_id=node.pk)
        else:
            missing.append(node.pk)
    if missing:
        warnings.warn(
            "Infrastructure leaves without matching feature layers: " + ", ".join(sorted(missing)),
            RuntimeWarning,
        )


class Migration(migrations.Migration):
    dependencies = [("map", "0025_merge_20261119_1248")]

    operations = [
        migrations.AddField(
            model_name="infrastructurenode",
            name="feature_layer",
            field=models.OneToOneField(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="infrastructure_node", to="map.featurelayer",
            ),
        ),
        migrations.RunPython(link_matching_leaves, migrations.RunPython.noop),
    ]
