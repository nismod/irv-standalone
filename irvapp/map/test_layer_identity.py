from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from map.models import Dataset, FeatureLayer, LayerIdentity, RasterLayer
from raster.models import RasterTileSource
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from django.core.management import call_command


class LayerIdentityTests(TestCase):
    def setUp(self):
        self.dataset = Dataset.objects.create(id='dataset', label='Dataset', group='hazards')
        self.source = RasterTileSource.objects.create(keys=['type'])

    def test_ids_are_unique_across_layer_types_and_identity_is_protected(self):
        feature = FeatureLayer.objects.create(layer_name='roads', sector='', subsector='', asset_type='')
        self.assertEqual(feature.identity.pk, 'roads')
        with self.assertRaises(IntegrityError), transaction.atomic():
            LayerIdentity.objects.filter(pk='roads').update(kind='raster')
        with self.assertRaises(IntegrityError), transaction.atomic():
            RasterLayer.objects.create(id='roads', tile_source=self.source,
                label='Raster', quantity='', unit='', stacking_order=0, display_order=0)
        with self.assertRaises(ProtectedError):
            LayerIdentity.objects.get(pk='roads').delete()
        feature.delete()
        LayerIdentity.objects.get(pk='roads').delete()
        LayerIdentity.objects.create(id='roads', kind='raster', dataset=self.dataset)
        raster = RasterLayer.objects.create(id='roads', tile_source=self.source,
            label='Raster', quantity='', unit='', stacking_order=0, display_order=0)
        self.assertEqual(LayerIdentity.objects.get(pk='roads').kind, 'raster')
        with self.assertRaises(IntegrityError), transaction.atomic():
            FeatureLayer.objects.create(layer_name='roads', sector='', subsector='', asset_type='')
        raster.delete()
        self.assertTrue(LayerIdentity.objects.filter(pk='roads').exists())

    def test_direct_sql_requires_matching_identity_and_kind(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO feature_layers (layer_name, sector, subsector, asset_type) VALUES (%s, %s, %s, %s)", ['missing', '', '', ''])
        LayerIdentity.objects.create(id='legacy', kind='feature')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO feature_layers (layer_name, sector, subsector, asset_type) VALUES (%s, %s, %s, %s)", ['legacy', '', '', ''])
        self.assertEqual(FeatureLayer.objects.get(pk='legacy').identity_id, 'legacy')
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO raster_layers (id, tile_source_id, label, quantity, unit, stacking_order, display_order) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    ['legacy', self.source.pk, 'Raster', '', '', 0, 0])

    def test_rename_collision_keeps_original_identity(self):
        FeatureLayer.objects.create(layer_name='feature', sector='', subsector='', asset_type='')
        LayerIdentity.objects.create(id='raster', kind='raster', dataset=self.dataset)
        RasterLayer.objects.create(id='raster', tile_source=self.source,
            label='Raster', quantity='', unit='', stacking_order=0, display_order=0)
        with self.assertRaises(IntegrityError), transaction.atomic():
            FeatureLayer.objects.filter(pk='feature').update(identity_id='raster')
        self.assertEqual(LayerIdentity.objects.get(pk='feature').kind, 'feature')
        self.assertEqual(LayerIdentity.objects.get(pk='raster').kind, 'raster')

    def test_model_validation_rejects_identity_for_other_layer_kind(self):
        identity = LayerIdentity.objects.create(id='raster', kind='raster')
        layer = FeatureLayer(identity=identity, sector='', subsector='', asset_type='')
        with self.assertRaises(ValidationError) as error:
            layer.clean()
        self.assertIn('identity', error.exception.message_dict)

    def test_existing_layer_accepts_bulk_ignore_and_sql_upsert(self):
        feature = FeatureLayer.objects.create(layer_name='roads', sector='', subsector='', asset_type='')
        FeatureLayer.objects.bulk_create(
            [FeatureLayer(layer_name='roads', sector='', subsector='', asset_type='')],
            ignore_conflicts=True,
        )
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO feature_layers (layer_name, sector, subsector, asset_type) VALUES (%s, %s, %s, %s) ON CONFLICT (layer_name) DO UPDATE SET sector = EXCLUDED.sector", ['roads', 'transport', '', ''])
        feature.refresh_from_db()
        self.assertEqual(feature.sector, 'transport')
        self.assertEqual(FeatureLayer.objects.filter(pk='roads').count(), 1)

    def test_default_fixture_round_trip(self):
        feature = FeatureLayer.objects.create(layer_name='roads', sector='', subsector='', asset_type='')
        output = StringIO()
        call_command('dumpdata', 'map', stdout=output, verbosity=0)
        feature.delete()
        LayerIdentity.objects.get(pk='roads').delete()
        with TemporaryDirectory() as directory:
            fixture = Path(directory) / 'fixture.json'
            fixture.write_text(output.getvalue())
            call_command('loaddata', str(fixture), verbosity=0)
        self.assertEqual(FeatureLayer.objects.get(pk='roads').identity_id, 'roads')


class ConcurrentLayerIdentityTests(TransactionTestCase):
    def test_simultaneous_cross_type_inserts_cannot_share_an_id(self):
        dataset = Dataset.objects.create(id='dataset', label='Dataset', group='hazards')
        source = RasterTileSource.objects.create(keys=['type'])
        barrier = Barrier(2)

        def insert(kind):
            from django.db import connections
            try:
                barrier.wait(timeout=5)
                with transaction.atomic():
                    LayerIdentity.objects.get_or_create(pk='concurrent', defaults={'kind': kind, 'dataset_id': dataset.pk})
                    if kind == 'feature':
                        FeatureLayer.objects.create(layer_name='concurrent', sector='', subsector='', asset_type='')
                    else:
                        RasterLayer.objects.create(id='concurrent', tile_source_id=source.pk,
                            label='Raster', quantity='', unit='', stacking_order=0, display_order=0)
                return 'created'
            except IntegrityError:
                return 'duplicate'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(insert, ['feature', 'raster']))
        self.assertCountEqual(outcomes, ['created', 'duplicate'])
        self.assertEqual(LayerIdentity.objects.filter(pk='concurrent').count(), 1)


class LayerIdentityMigrationTests(TransactionTestCase):
    def test_rollback_rejects_unattached_identities(self):
        before = [('map', '0030_remove_dataset_quantity_unit'), ('raster', '0010_rastertilesource_path_template')]
        LayerIdentity.objects.create(id='reserved', kind='feature')
        try:
            with self.assertRaisesRegex(RuntimeError, 'reserved'):
                MigrationExecutor(connection).migrate(before)
        finally:
            executor = MigrationExecutor(connection)
            apps = executor.loader.project_state([
                ('map', '0031_layeridentity'), ('raster', '0010_rastertilesource_path_template'),
            ]).apps
            apps.get_model('map', 'LayerIdentity').objects.filter(pk='reserved').delete()
            executor.migrate(executor.loader.graph.leaf_nodes())

    def test_existing_layers_become_identity_relations_without_triggers(self):
        before = [('map', '0030_remove_dataset_quantity_unit'), ('raster', '0010_rastertilesource_path_template')]
        after = [('map', '0031_layeridentity'), ('raster', '0010_rastertilesource_path_template')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        dataset = apps.get_model('map', 'Dataset').objects.create(id='dataset', label='Dataset', group='hazards')
        source = apps.get_model('raster', 'RasterTileSource').objects.create(keys=['type'])
        feature = apps.get_model('map', 'FeatureLayer').objects.create(layer_name='roads', sector='', subsector='', asset_type='')
        apps.get_model('map', 'Feature').objects.create(
            layer=feature, string_id='road-1', properties={}, geom=Point(0, 0, srid=4326),
        )
        apps.get_model('map', 'InfrastructureTree').objects.create(node_id='road-node', node_name='Roads', feature_layer=feature)
        apps.get_model('map', 'RasterLayer').objects.create(id='rain', dataset=dataset, tile_source=source,
            label='Rain', quantity='depth', unit='m', stacking_order=2, display_order=4)
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            self.assertEqual(apps.get_model('map', 'FeatureLayer').objects.get(pk='roads').identity_id, 'roads')
            self.assertEqual(apps.get_model('map', 'RasterLayer').objects.get(pk='rain').identity_id, 'rain')
            self.assertEqual(apps.get_model('map', 'InfrastructureTree').objects.get(pk='road-node').feature_layer_id, 'roads')
            self.assertEqual(apps.get_model('map', 'Feature').objects.get(string_id='road-1').layer_id, 'roads')
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_trigger WHERE tgname IN ('feature_layer_identity', 'raster_layer_identity') AND NOT tgisinternal")
                self.assertEqual(cursor.fetchone()[0], 0)
            executor = MigrationExecutor(connection)
            executor.migrate(before)
            apps = executor.loader.project_state(before).apps
            self.assertEqual(apps.get_model('map', 'Feature').objects.get(string_id='road-1').layer_id, 'roads')
            self.assertTrue(apps.get_model('map', 'RasterLayer').objects.filter(pk='rain').exists())
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())

    def test_existing_collisions_stop_migration(self):
        before = [('map', '0030_remove_dataset_quantity_unit'), ('raster', '0010_rastertilesource_path_template')]
        after = [('map', '0031_layeridentity'), ('raster', '0010_rastertilesource_path_template')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        dataset = apps.get_model('map', 'Dataset').objects.create(id='dataset', label='Dataset', group='hazards')
        source = apps.get_model('raster', 'RasterTileSource').objects.create(keys=['type'])
        apps.get_model('map', 'FeatureLayer').objects.create(layer_name='duplicate', sector='', subsector='', asset_type='')
        Raster = apps.get_model('map', 'RasterLayer')
        Raster.objects.create(id='duplicate', dataset=dataset, tile_source=source, label='Raster',
                              quantity='', unit='', stacking_order=0, display_order=0)
        try:
            with self.assertRaisesRegex(RuntimeError, 'duplicate'):
                MigrationExecutor(connection).migrate(after)
        finally:
            Raster.objects.filter(pk='duplicate').delete()
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
