import django.db.models.deletion
from django.db import migrations, models


def move_datasets_to_identities(apps, schema_editor):
    Identity = apps.get_model('map', 'LayerIdentity')
    alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('LOCK TABLE feature_layers, raster_layers, layer_identities IN SHARE ROW EXCLUSIVE MODE')
    for name in ('FeatureLayer', 'RasterLayer'):
        Layer = apps.get_model('map', name)
        for identity_id, dataset_id in Layer.objects.using(alias).values_list('pk', 'dataset_id').iterator():
            Identity.objects.using(alias).filter(pk=identity_id).update(dataset_id=dataset_id)


def restore_layer_datasets(apps, schema_editor):
    Identity = apps.get_model('map', 'LayerIdentity')
    Feature = apps.get_model('map', 'FeatureLayer')
    Raster = apps.get_model('map', 'RasterLayer')
    alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('LOCK TABLE feature_layers, raster_layers, layer_identities IN SHARE ROW EXCLUSIVE MODE')
    attached = set(Feature.objects.using(alias).values_list('pk', flat=True))
    attached.update(Raster.objects.using(alias).values_list('pk', flat=True))
    unattached = list(Identity.objects.using(alias).filter(dataset__isnull=False).exclude(pk__in=attached).values_list('pk', flat=True))
    if unattached:
        raise RuntimeError('Cannot reverse: identities have dataset assignments without layers: ' + ', '.join(sorted(unattached)))
    for Layer in (Feature, Raster):
        for identity_id, dataset_id in Identity.objects.using(alias).filter(pk__in=Layer.objects.using(alias).values('pk')).values_list('pk', 'dataset_id').iterator():
            if Layer is Raster and dataset_id is None:
                raise RuntimeError(f'Cannot reverse: raster layer {identity_id!r} has no dataset.')
            Layer.objects.using(alias).filter(pk=identity_id).update(dataset_id=dataset_id)


class Migration(migrations.Migration):
    dependencies = [('map', '0031_layeridentity')]

    operations = [
        migrations.AddField(
            model_name='layeridentity', name='dataset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='layer_identities', to='map.dataset'),
        ),
        migrations.AlterField(
            model_name='rasterlayer', name='dataset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='raster_layers', to='map.dataset'),
        ),
        migrations.RunPython(move_datasets_to_identities, restore_layer_datasets),
        migrations.RemoveField(model_name='featurelayer', name='dataset'),
        migrations.RemoveField(model_name='rasterlayer', name='dataset'),
    ]
