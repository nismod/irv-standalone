from django.contrib.auth.models import User
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from map.models import FeatureLayer, FeatureLayerStyle


class FeatureLayerStyleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        FeatureLayerStyle.objects.update_or_create(pk="road_edges_motorway", defaults={
            "label": "Roads", "style_type": "line", "color": "#123456",
        })

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
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes()))
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps
        Identity = old_apps.get_model("map", "LayerIdentity")
        Layer = old_apps.get_model("map", "FeatureLayer")
        OldStyle = old_apps.get_model("map", "NetworkLayerStyle")
        OldStyle.objects.update_or_create(pk="road_edges_motorway", defaults={
            "label": "Roads", "style_type": "line", "color": "#123456",
        })
        OldStyle.objects.update_or_create(pk="elec_edges_high", defaults={
            "label": "Power", "style_type": "line", "color": "#abcdef",
        })
        Identity.objects.create(id="road_edges_motorway", kind="feature")
        Layer.objects.create(identity_id="road_edges_motorway", sector="", subsector="", asset_type="")
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        apps = executor.loader.project_state([self.migrate_to]).apps
        Style = apps.get_model("map", "FeatureLayerStyle")
        linked = Style.objects.get(pk="road_edges_motorway")
        self.assertEqual(linked.feature_layer_id, "road_edges_motorway")
        self.assertEqual(linked.color, "#123456")
        self.assertIsNone(Style.objects.get(pk="elec_edges_high").feature_layer_id)
        self.assertIn("feature_layer_styles", connection.introspection.table_names())
        self.assertNotIn("network_layer_styles", connection.introspection.table_names())


class FeatureLayerStylePermissionMigrationTests(TransactionTestCase):
    def test_preserves_direct_and_group_grants_including_existing_destinations(self):
        before = ("map", "0033_feature_layer_styles")
        after = ("map", "0034_feature_layer_style_permissions")
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes()))
        MigrationExecutor(connection).migrate([before])
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType

        old_type, _ = ContentType.objects.get_or_create(app_label="map", model="networklayerstyle")
        new_type, _ = ContentType.objects.get_or_create(app_label="map", model="featurelayerstyle")
        user = User.objects.create_user(username="old-staff", is_staff=True)
        destination_user = User.objects.create_user(username="new-staff", is_staff=True)
        group = Group.objects.create(name="style-editors")
        user.groups.add(group)
        for action in ("add", "change", "delete", "view"):
            old, _ = Permission.objects.get_or_create(
                content_type=old_type, codename=f"{action}_networklayerstyle", defaults={"name": "Old permission"},
            )
            user.user_permissions.add(old)
            group.permissions.add(old)
        existing, _ = Permission.objects.get_or_create(
            content_type=new_type, codename="change_featurelayerstyle", defaults={"name": "New permission"},
        )
        destination_user.user_permissions.add(existing)
        renamed_type_permission, _ = Permission.objects.get_or_create(
            content_type=new_type, codename="delete_networklayerstyle", defaults={"name": "Old permission"},
        )
        destination_user.user_permissions.add(renamed_type_permission)

        MigrationExecutor(connection).migrate([after])
        for action in ("add", "change", "delete", "view"):
            self.assertTrue(User.objects.get(pk=user.pk).has_perm(f"map.{action}_featurelayerstyle"))
            permission = Permission.objects.get(content_type=new_type, codename=f"{action}_featurelayerstyle")
            self.assertTrue(group.permissions.filter(pk=permission.pk).exists())
            self.assertTrue(User.objects.get(pk=user.pk).user_permissions.filter(pk=permission.pk).exists())
        self.assertTrue(User.objects.get(pk=destination_user.pk).has_perm("map.change_featurelayerstyle"))
        self.assertTrue(User.objects.get(pk=destination_user.pk).has_perm("map.delete_featurelayerstyle"))
        self.assertEqual(Permission.objects.get(content_type=new_type, codename="change_featurelayerstyle").pk, existing.pk)
        self.assertFalse(Permission.objects.filter(content_type=old_type, codename__endswith="_networklayerstyle").exists())

        MigrationExecutor(connection).migrate([before])
        self.assertTrue(User.objects.get(pk=user.pk).has_perm("map.change_networklayerstyle"))
        self.assertTrue(User.objects.get(pk=destination_user.pk).has_perm("map.change_networklayerstyle"))
