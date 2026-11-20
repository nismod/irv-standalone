from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from map.models import Dataset, RasterLayer
from raster.models import RasterTileSource


class RasterLayerAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="raster-user")
        self.group = Group.objects.create(name="raster-access")
        self.user.groups.add(self.group)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.source = RasterTileSource.objects.create(keys=["region"], database="test.sqlite")
        self.dataset = Dataset.objects.create(
            id="floods", label="Floods", group="hazards",

        )
        self.dataset.access_groups.add(self.group)
        for name in ("river", "coastal"):
            RasterLayer.objects.create(
                id=name, dataset=self.dataset, tile_source=self.source, label=name,
                quantity="depth", unit="m", stacking_order=0, display_order=0,
            )
        restricted = Dataset.objects.create(
            id="restricted", label="Restricted", group="hazards",
        )
        restricted_source = RasterTileSource.objects.create(keys=["region"], database="private.sqlite")
        RasterLayer.objects.create(
            id="private", dataset=restricted, tile_source=restricted_source, label="Private",
            quantity="depth", unit="m", stacking_order=0, display_order=0,
        )

    @patch("raster.views.tiles._get_singleband_image", return_value=b"png")
    def test_layer_endpoints_inherit_group_access(self, render):
        response = self.client.get('/map/raster-layers', {'group': 'hazards'})
        layers = {layer['id']: layer for layer in response.json()['results']}
        self.assertEqual(set(layers), {'river', 'coastal', 'private'})
        self.assertTrue(layers['river']['has_access'])
        self.assertTrue(layers['coastal']['has_access'])
        self.assertFalse(layers['private']['has_access'])
        self.assertEqual(layers['river']['dataset'], 'floods')
        self.assertEqual(self.client.get('/map/raster-layers/private').status_code, 403)
        self.assertEqual(self.client.get('/tiles/raster/river/x/0/0/0.png').status_code, 200)
        self.assertEqual(self.client.get('/tiles/raster/coastal/x/0/0/0.png').status_code, 200)
        self.assertEqual(self.client.get('/tiles/raster/private/x/0/0/0.png').status_code, 403)
        self.assertEqual(render.call_count, 2)

    @patch("raster.views.sources._source_options")
    @patch("raster.views.tiles._get_singleband_image", return_value=b"png")
    def test_shared_database_requires_access_to_all_datasets(self, render, domains):
        restricted = Dataset.objects.get(pk="restricted")
        self.source.keys = ['type']
        self.source.save(update_fields=['keys'])
        other_group = Group.objects.create(name="other-access")
        restricted.access_groups.add(other_group)
        # Separate source records can still point at the same physical database.
        alias = RasterTileSource.objects.create(keys=["type"], database="./test.sqlite")
        RasterLayer.objects.filter(pk="private").update(tile_source=alias)
        for path in ('/tiles/raster/river/coastal/0/0/0.png', '/tiles/raster/sources/river/domains'):
            self.assertEqual(self.client.get(path).status_code, 403)
        render.assert_not_called()
        domains.assert_not_called()
        self.assertFalse(next(row for row in self.client.get('/map/raster-layers').json()['results'] if row['id'] == 'river')['has_access'])
        self.user.groups.add(other_group)
        domains.return_value = []
        self.assertEqual(self.client.get('/tiles/raster/river/coastal/0/0/0.png').status_code, 200)
        self.assertEqual(self.client.get('/tiles/raster/sources/river/domains').status_code, 200)

    @patch("raster.views.sources._source_options")
    @patch("raster.views.tiles._get_singleband_image", return_value=b"png")
    def test_source_without_type_key_also_fails_closed(self, render, domains):
        RasterLayer.objects.filter(pk="private").update(tile_source=self.source)
        self.assertEqual(self.client.get('/tiles/raster/river/secret/0/0/0.png').status_code, 403)
        self.assertEqual(self.client.get('/tiles/raster/sources/river/domains').status_code, 403)
        render.assert_not_called()
        domains.assert_not_called()


class RasterLayerMigrationTests(TransactionTestCase):
    def test_quantity_and_unit_remain_on_raster_layers(self):
        before = [('map', '0029_remove_dataset_display_order_and_more'),
                  ('raster', '0010_rastertilesource_path_template')]
        after = [('map', '0030_remove_dataset_quantity_unit'),
                 ('raster', '0010_rastertilesource_path_template')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        Dataset = apps.get_model('map', 'Dataset')
        Layer = apps.get_model('map', 'RasterLayer')
        Source = apps.get_model('raster', 'RasterTileSource')
        source = Source.objects.create(keys=['type'])
        dataset = Dataset.objects.create(id='rain', label='Rain', group='hazards', quantity='old', unit='old')
        Layer.objects.create(id='rain', dataset=dataset, tile_source=source, label='Rain', quantity='depth', unit='m', stacking_order=0, display_order=0)
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            layer = apps.get_model('map', 'RasterLayer').objects.get(pk='rain')
            self.assertEqual((layer.quantity, layer.unit), ('depth', 'm'))
            executor = MigrationExecutor(connection)
            executor.migrate(before)
            restored = executor.loader.project_state(before).apps.get_model('map', 'Dataset').objects.get(pk='rain')
            self.assertEqual((restored.quantity, restored.unit), ('depth', 'm'))
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())

    def test_existing_datasets_and_shared_source_are_preserved(self):
        executor = MigrationExecutor(connection)
        old_target = [('map', '0026_infrastructure_node_feature_layer'),
                      ('raster', '0010_rastertilesource_path_template')]
        new_target = [('map', '0027_remove_dataset_tile_source_rasterlayer'),
                      ('raster', '0010_rastertilesource_path_template')]
        executor.migrate(old_target)
        old_apps = executor.loader.project_state(old_target).apps
        Source = old_apps.get_model('raster', 'RasterTileSource')
        Dataset = old_apps.get_model('map', 'Dataset')
        Group = old_apps.get_model('auth', 'Group')
        source = Source.objects.create(keys=['type'])
        group = Group.objects.create(name='migration-access')
        for name in ('river', 'coastal'):
            dataset = Dataset.objects.create(
                id=name, label=name.title(), group='hazards', quantity='depth', unit='m',
                tile_source_id=source.pk, stacking_order=2, display_order=1,
                color_scheme='blues', color_range=[0, 10],
            )
            dataset.access_groups.add(group)
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(new_target)
            new_apps = executor.loader.project_state(new_target).apps
            Layer = new_apps.get_model('map', 'RasterLayer')
            NewDataset = new_apps.get_model('map', 'Dataset')
            self.assertEqual(Layer.objects.count(), 2)
            for name in ('river', 'coastal'):
                layer = Layer.objects.get(pk=name)
                self.assertEqual(layer.dataset_id, name)
                self.assertEqual(layer.tile_source_id, source.pk)
                self.assertEqual(layer.color_range, [0, 10])
                self.assertEqual(list(NewDataset.objects.get(pk=name).access_groups.values_list('pk', flat=True)), [group.pk])
            latest_target = [('map', '0028_remove_dataset_colours'),
                             ('raster', '0010_rastertilesource_path_template')]
            executor = MigrationExecutor(connection)
            executor.migrate(latest_target)
            latest_apps = executor.loader.project_state(latest_target).apps
            latest_layer = latest_apps.get_model('map', 'RasterLayer').objects.get(pk='river')
            self.assertEqual(latest_layer.color_scheme, 'blues')
            self.assertEqual(latest_layer.color_range, [0, 10])
            executor = MigrationExecutor(connection)
            executor.migrate(new_target)
            restored = executor.loader.project_state(new_target).apps.get_model('map', 'Dataset')
            self.assertEqual(restored.objects.get(pk='river').color_range, [0, 10])
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
