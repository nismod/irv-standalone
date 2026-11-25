from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from map.models import FeatureLayer, InfrastructureTree


class InfrastructureTreeTests(TestCase):
    def setUp(self):
        self.layer = FeatureLayer.objects.create(
            layer_name="road_edges_class_a", sector="transport",
            subsector="road", asset_type="CLASS A",
        )
        self.root = InfrastructureTree.objects.create(node_id="roads", node_name="Roads")
        self.leaf = InfrastructureTree.objects.create(
            node_id="class-a", node_name="Class A", parent=self.root, feature_layer=self.layer,
        )

    def test_tree_api_returns_explicit_layer(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.create_user(username="tree-user"))
        response = client.get("/map/infrastructure-tree")
        root = response.json()["results"][0]
        self.assertIsNone(root["feature_layer"])
        self.assertEqual(root["children"][0]["feature_layer"], self.layer.pk)

    def test_layer_is_unique_and_protected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InfrastructureTree.objects.create(node_id="other", node_name="Other", feature_layer=self.layer)
        with self.assertRaises(ProtectedError):
            self.layer.delete()

    def test_parent_and_child_validation(self):
        self.root.feature_layer = self.layer
        with self.assertRaises(ValidationError):
            self.root.clean()
        child = InfrastructureTree(node_id="child", node_name="Child", parent=self.leaf)
        with self.assertRaises(ValidationError):
            child.clean()

    def test_backfill_matches_only_leaves_and_reports_missing(self):
        self.leaf.feature_layer = None
        self.leaf.save()
        matching = InfrastructureTree.objects.create(
            node_id=self.layer.pk, node_name="Matching", parent=self.root,
        )
        migration = import_module("map.migrations.0026_infrastructure_node_feature_layer")
        historical_apps = SimpleNamespace(
            get_model=lambda app_label, model_name: (
                InfrastructureTree if (app_label, model_name) == ("map", "InfrastructureNode")
                else apps.get_model(app_label, model_name)
            ),
        )
        with patch("warnings.warn") as warn:
            migration.link_matching_leaves(historical_apps, SimpleNamespace(connection=connection))
        matching.refresh_from_db()
        self.root.refresh_from_db()
        self.assertEqual(matching.feature_layer_id, self.layer.pk)
        self.assertIsNone(self.root.feature_layer_id)
        self.assertIn("class-a", warn.call_args.args[0])
