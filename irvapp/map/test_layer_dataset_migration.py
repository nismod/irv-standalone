from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class LayerDatasetMigrationTests(TransactionTestCase):
    def test_moves_assignments_to_identities_and_restores_them_on_rollback(self):
        before = [('map', '0031_layeridentity'), ('raster', '0010_rastertilesource_path_template')]
        after = [('map', '0032_remove_featurelayer_dataset_and_more'), ('raster', '0010_rastertilesource_path_template')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        Dataset = apps.get_model('map', 'Dataset')
        Identity = apps.get_model('map', 'LayerIdentity')
        Feature = apps.get_model('map', 'FeatureLayer')
        Raster = apps.get_model('map', 'RasterLayer')
        Source = apps.get_model('raster', 'RasterTileSource')
        roads = Dataset.objects.create(id='roads', label='Roads', group='infrastructure')
        rain = Dataset.objects.create(id='rain', label='Rain', group='hazards')
        source = Source.objects.create(keys=['type'])
        Identity.objects.create(id='road-layer', kind='feature')
        Identity.objects.create(id='unlinked', kind='feature')
        Identity.objects.create(id='rain-layer', kind='raster')
        Identity.objects.create(id='orphan', kind='feature')
        Feature.objects.create(identity_id='road-layer', dataset=roads, sector='', subsector='', asset_type='')
        Feature.objects.create(identity_id='unlinked', dataset=None, sector='', subsector='', asset_type='')
        Raster.objects.create(identity_id='rain-layer', dataset=rain, tile_source=source,
                              label='Rain', quantity='depth', unit='m', stacking_order=2, display_order=3)
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            Identity = apps.get_model('map', 'LayerIdentity')
            self.assertEqual(Identity.objects.get(pk='road-layer').dataset_id, 'roads')
            self.assertEqual(Identity.objects.get(pk='rain-layer').dataset_id, 'rain')
            self.assertIsNone(Identity.objects.get(pk='unlinked').dataset_id)
            self.assertIsNone(Identity.objects.get(pk='orphan').dataset_id)
            executor = MigrationExecutor(connection)
            executor.migrate(before)
            apps = executor.loader.project_state(before).apps
            self.assertEqual(apps.get_model('map', 'FeatureLayer').objects.get(pk='road-layer').dataset_id, 'roads')
            self.assertIsNone(apps.get_model('map', 'FeatureLayer').objects.get(pk='unlinked').dataset_id)
            self.assertEqual(apps.get_model('map', 'RasterLayer').objects.get(pk='rain-layer').dataset_id, 'rain')
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())

    def test_rollback_rejects_dataset_on_unattached_identity(self):
        from map.models import Dataset, LayerIdentity
        dataset = Dataset.objects.create(id='reserved', label='Reserved', group='infrastructure')
        identity = LayerIdentity.objects.create(id='orphan', kind='feature', dataset=dataset)
        before = [('map', '0031_layeridentity'), ('raster', '0010_rastertilesource_path_template')]
        try:
            with self.assertRaisesRegex(RuntimeError, 'orphan'):
                MigrationExecutor(connection).migrate(before)
        finally:
            identity.delete()
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())

    def test_rollback_rejects_unassigned_raster_without_losing_data(self):
        from map.models import LayerIdentity, RasterLayer
        from raster.models import RasterTileSource
        source = RasterTileSource.objects.create(keys=['type'])
        RasterLayer.objects.create(id='rain', tile_source=source, label='Rain',
                                   quantity='depth', unit='m', stacking_order=0, display_order=0)
        before = [('map', '0031_layeridentity'), ('raster', '0010_rastertilesource_path_template')]
        try:
            with self.assertRaisesRegex(RuntimeError, 'raster layer.*rain.*no dataset'):
                MigrationExecutor(connection).migrate(before)
            self.assertTrue(RasterLayer.objects.filter(pk='rain').exists())
            self.assertIsNone(LayerIdentity.objects.get(pk='rain').dataset_id)
        finally:
            RasterLayer.objects.filter(pk='rain').delete()
            LayerIdentity.objects.filter(pk='rain').delete()
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
