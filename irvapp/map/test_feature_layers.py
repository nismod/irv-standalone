from unittest.mock import patch
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from map.models import Dataset, FeatureLayer


class FeatureLayerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='feature-user')
        self.group = Group.objects.create(name='feature-access')
        self.user.groups.add(self.group)
        self.dataset = Dataset.objects.create(id='roads', label='Roads', group='infrastructure')
        self.dataset.access_groups.add(self.group)
        for name in ('road_edges_motorway', 'road_edges_class_a'):
            FeatureLayer.objects.create(
                layer_name=name, dataset=self.dataset, sector='transport', subsector='road',
                asset_type=name, stacking_order=2, display_order=3,
            )
        FeatureLayer.objects.create(layer_name='unlinked', sector='', subsector='', asset_type='')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_layer_catalog_inherits_dataset_access(self):
        response = self.client.get('/map/feature-layers')
        layers = {layer['layer_name']: layer for layer in response.json()['results']}
        self.assertTrue(layers['road_edges_motorway']['has_access'])
        self.assertTrue(layers['road_edges_class_a']['has_access'])
        self.assertFalse(layers['unlinked']['has_access'])
        self.assertEqual(layers['road_edges_motorway']['dataset'], 'roads')
        self.assertEqual(layers['road_edges_motorway']['display_order'], 3)
        self.assertEqual(self.client.get('/map/feature-layers/unlinked').status_code, 403)
        self.dataset.access_groups.clear()
        self.assertEqual(self.client.get('/map/feature-layers/road_edges_motorway').status_code, 403)
        self.assertEqual(self.client.get('/map/feature-layers/road_edges_class_a').status_code, 403)

    @patch('vector_proxy.views.urlopen')
    def test_tile_proxy_uses_layer_dataset_not_matching_id(self, urlopen):
        self.dataset.access_groups.clear()
        unrelated = Dataset.objects.create(id='road_edges_motorway', label='Other', group='infrastructure')
        unrelated.access_groups.add(self.group)
        response = self.client.get('/tiles/vector/data/road_edges_motorway.json')
        self.assertEqual(response.status_code, 403)
        urlopen.assert_not_called()
        self.assertEqual(self.client.get('/tiles/vector/data/unlinked.json').status_code, 403)

    def test_post_ingestion_link_command_handles_new_and_existing_layers(self):
        Dataset.objects.create(id='unlinked', label='New', group='infrastructure')
        Dataset.objects.create(id='late', label='Late', group='infrastructure')
        layer = FeatureLayer.objects.create(layer_name='late', sector='', subsector='', asset_type='')
        unmatched = FeatureLayer.objects.create(layer_name='missing', sector='', subsector='', asset_type='')
        output = StringIO()
        call_command('link_feature_layers', stdout=output)
        layer.refresh_from_db()
        unmatched.refresh_from_db()
        self.assertEqual(layer.dataset_id, 'late')
        self.assertEqual(FeatureLayer.objects.get(pk='unlinked').dataset_id, 'unlinked')
        self.assertIsNone(unmatched.dataset_id)
        self.assertIn('missing', output.getvalue())
        self.assertEqual(FeatureLayer.objects.get(pk='road_edges_motorway').dataset_id, 'roads')
        output = StringIO()
        call_command('link_feature_layers', stdout=output)
        self.assertIn('Linked 0', output.getvalue())


class FeatureLayerMigrationTests(TransactionTestCase):
    def test_rollback_rejects_dataset_without_recoverable_order(self):
        before = [('map', '0028_remove_dataset_colours'), ('raster', '0010_rastertilesource_path_template')]
        after = [('map', '0029_remove_dataset_display_order_and_more'), ('raster', '0010_rastertilesource_path_template')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        Dataset = apps.get_model('map', 'Dataset')
        Dataset.objects.create(id='empty', label='Empty', group='infrastructure', stacking_order=7, display_order=4)
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            executor = MigrationExecutor(connection)
            with self.assertRaisesRegex(RuntimeError, 'no layer'):
                executor.migrate(before)
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())

    def test_matching_layers_link_and_copy_order(self):
        before = [('map', '0028_remove_dataset_colours'), ('raster', '0010_rastertilesource_path_template')]
        after = [('map', '0029_remove_dataset_display_order_and_more'), ('raster', '0010_rastertilesource_path_template')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        Dataset = apps.get_model('map', 'Dataset')
        Layer = apps.get_model('map', 'FeatureLayer')
        Dataset.objects.create(id='roads', label='Roads', group='infrastructure', stacking_order=7, display_order=4)
        Layer.objects.create(layer_name='roads', sector='transport', subsector='road', asset_type='edge')
        Layer.objects.create(layer_name='unknown', sector='', subsector='', asset_type='')
        try:
            executor = MigrationExecutor(connection)
            with self.assertWarnsRegex(RuntimeWarning, 'unknown'):
                executor.migrate(after)
            Layer = executor.loader.project_state(after).apps.get_model('map', 'FeatureLayer')
            linked = Layer.objects.get(pk='roads')
            self.assertEqual((linked.dataset_id, linked.stacking_order, linked.display_order), ('roads', 7, 4))
            self.assertIsNone(Layer.objects.get(pk='unknown').dataset_id)
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
