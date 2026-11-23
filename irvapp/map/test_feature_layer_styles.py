from django.contrib.auth.models import User
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from map.models import FeatureLayer, FeatureLayerStyle


class FeatureLayerStyleTests(TestCase):
    def test_style_links_to_matching_feature_layer_and_preserves_api(self):
        layer = FeatureLayer.objects.create(layer_name="road_edges_motorway", sector="", subsector="", asset_type="")
        style = FeatureLayerStyle.objects.get(pk=layer.pk)
        style.feature_layer = layer
        style.save()
        self.assertEqual(layer.style.pk, layer.pk)
        client = APIClient()
        client.force_authenticate(User.objects.create_user(username="style-user"))
        response = client.get("/map/network-layer-styles/road_edges_motorway")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], layer.pk)
        self.assertEqual(response.data["color"], style.color)
        with self.assertRaises(ProtectedError):
            layer.delete()

    def test_link_must_match_style_id(self):
        layer = FeatureLayer.objects.create(layer_name="different", sector="", subsector="", asset_type="")
        with self.assertRaises(IntegrityError), transaction.atomic():
            FeatureLayerStyle.objects.filter(pk="road_edges_motorway").update(feature_layer=layer)


class FeatureLayerStyleMigrationTests(TransactionTestCase):
    migrate_from = ("map", "0032_remove_featurelayer_dataset_and_more")
    migrate_to = ("map", "0033_feature_layer_styles")

    def test_migration_links_matching_styles_and_preserves_unmatched(self):
        executor = MigrationExecutor(connection)
        self.addCleanup(lambda: MigrationExecutor(connection).migrate([self.migrate_to]))
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps
        Identity = old_apps.get_model("map", "LayerIdentity")
        Layer = old_apps.get_model("map", "FeatureLayer")
        OldStyle = old_apps.get_model("map", "NetworkLayerStyle")
        style = OldStyle.objects.get(pk="road_edges_motorway")
        old_color = style.color
        Identity.objects.create(id="road_edges_motorway", kind="feature")
        Layer.objects.create(identity_id="road_edges_motorway", sector="", subsector="", asset_type="")
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        apps = executor.loader.project_state([self.migrate_to]).apps
        Style = apps.get_model("map", "FeatureLayerStyle")
        linked = Style.objects.get(pk="road_edges_motorway")
        self.assertEqual(linked.feature_layer_id, "road_edges_motorway")
        self.assertEqual(linked.color, old_color)
        self.assertIsNone(Style.objects.get(pk="elec_edges_high").feature_layer_id)
        self.assertIn("feature_layer_styles", connection.introspection.table_names())
        self.assertNotIn("network_layer_styles", connection.introspection.table_names())
