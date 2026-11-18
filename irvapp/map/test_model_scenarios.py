import json
from urllib.parse import urlencode

from django.contrib.auth.models import Group, User
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from map.models import (
    AdaptationCostBenefit, DamagesExpected, Dataset, Feature, FeatureLayer, ModelParameterSet,
)


class ModelScenarioTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="scenarios")
        self.client.force_authenticate(self.user)
        self.features = []
        for name, sector in (("roads", "transport"), ("power", "energy")):
            layer = FeatureLayer.objects.create(
                layer_name=name, sector=sector, subsector=name, asset_type="edge",
            )
            self.features.append(Feature.objects.create(
                layer=layer, string_id=name, properties={}, geom=Point(0, 0, srid=4326),
            ))

    def damage(self, feature, parameters, hazard="flood", protection=0, amount=10):
        return DamagesExpected.objects.create(
            feature=feature, hazard=hazard, protection_standard=protection,
            parameter_set=ModelParameterSet.for_values("damages_expected", parameters),
            ead_mean=amount,
        )

    def test_requires_authentication_and_valid_model(self):
        self.assertEqual(self.client.get("/map/model-scenarios/unknown").status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/map/model-scenarios/damages_expected").status_code, 403)

    def test_returns_only_used_combinations_in_scope_with_json_types(self):
        parameters = {"gwl": 2, "slr": 0.5, "config": {"members": [1, "1"]}}
        self.damage(self.features[0], parameters)
        self.damage(self.features[1], parameters)
        self.damage(self.features[1], {"gwl": 4})
        ModelParameterSet.for_values("damages_expected", {"unused": True})
        response = self.client.get("/map/model-scenarios/damages_expected", {"sector": "transport"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "hazard": "flood", "parameters": parameters, "protection_standard": 0,
        }])
        response = self.client.get("/map/model-scenarios/damages_expected", {"layer": ["roads", "power"]})
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(self.client.get("/map/model-scenarios/damages_expected", {"layer": "missing"}).json(), [])

    def test_preserves_hazard_and_protection_combinations(self):
        self.damage(self.features[0], {"rcp": "4.5", "epoch": 2050}, protection=0)
        self.damage(self.features[0], {"rcp": "4.5", "epoch": 2050}, protection=100)
        self.damage(self.features[0], {"gwl": 2}, hazard="heat")
        rows = self.client.get("/map/model-scenarios/damages_expected").json()
        self.assertEqual(len(rows), 3)
        rows = self.client.get("/map/model-scenarios/damages_expected", {"hazard": "flood"}).json()
        self.assertEqual({row["protection_standard"] for row in rows}, {0, 100})

    def test_groups_combinations_before_checking_the_feature_scope(self):
        self.damage(self.features[0], {"gwl": 2})
        self.damage(self.features[1], {"gwl": 4})
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                "/map/model-scenarios/damages_expected", {"layer": "roads"},
            )
        self.assertEqual([row["parameters"] for row in response.json()], [{"gwl": 2}])
        discovery_queries = [query["sql"] for query in queries if 'WITH RECURSIVE scenario_keys' in query["sql"]]
        self.assertEqual(len(discovery_queries), 1)
        # Discovery must seek between index prefixes, not scan every result
        # with DISTINCT or join every duplicate to a feature geometry row.
        self.assertNotIn('JOIN "features"', discovery_queries[0])
        self.assertNotIn('SELECT DISTINCT', discovery_queries[0])

    def test_adaptation_options_and_protector_scope(self):
        for protector, name in ((123, "Wall"), (456, "Raise")):
            AdaptationCostBenefit.objects.create(
                feature=self.features[0], hazard="flood", protector_feature_id=protector,
                parameter_set=ModelParameterSet.for_values("adaptation", {"gwl": 2, "slr": 0.5}),
                adaptation_name=name, adaptation_protection_level=50,
            )
        response = self.client.get("/map/model-scenarios/adaptation", {"protector_id": 123})
        self.assertEqual(response.json(), [{
            "hazard": "flood", "parameters": {"gwl": 2, "slr": 0.5},
            "adaptation_name": "Wall", "adaptation_protection_level": 50.0,
        }])
        self.assertEqual(self.client.get("/map/model-scenarios/adaptation", {"protector_id": "bad"}).status_code, 400)
        self.assertEqual(self.client.get("/map/model-scenarios/damages_expected", {"protector_id": 123}).status_code, 400)

    def test_layer_bounds_do_not_include_interleaved_features_from_other_layers(self):
        Feature.objects.create(
            layer=self.features[0].layer, string_id="last-road", properties={},
            geom=Point(1, 1, srid=4326),
        )
        self.damage(self.features[0], {"gwl": 2})
        self.damage(self.features[1], {"gwl": 4})
        rows = self.client.get(
            "/map/model-scenarios/damages_expected", {"layer": "roads"},
        ).json()
        self.assertEqual([row["parameters"] for row in rows], [{"gwl": 2}])

    def test_hazard_permissions_apply_to_discovery_map_values_and_sorted_totals(self):
        dataset = Dataset.objects.create(
            id="coastal", label="Coastal", group="hazards", quantity="depth", unit="m",
            stacking_order=0, display_order=0,
        )
        parameters = {"gwl": 2}
        self.damage(self.features[0], parameters, hazard="fluvial", amount=10)
        self.damage(self.features[0], parameters, hazard="coastal", amount=90)

        def check(expected_total, hazards):
            response = self.client.get("/map/model-scenarios/damages_expected", {"layer": "roads"})
            self.assertEqual({row["hazard"] for row in response.json()}, hazards)
            query = {
                "layer": "roads", "field": "ead_mean",
                "dimensions": json.dumps({"hazard": "all", "parameters": parameters, "protection_standard": 0}),
            }
            response = self.client.post(
                "/map/attributes/damages_expected?" + urlencode(query),
                {"ids": [self.features[0].pk]}, format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[str(self.features[0].pk)], expected_total)
            response = self.client.get("/map/features/sorted-by/damages_expected", query)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["items"][0]["value"], expected_total)

        # A result hazard with no raster dataset (fluvial) remains available.
        check(10, {"fluvial"})
        group = Group.objects.create(name="coastal-data")
        dataset.access_groups.add(group)
        self.user.groups.add(group)
        check(100, {"fluvial", "coastal"})
        self.user.groups.remove(group)
        self.user.is_superuser = True
        self.user.save(update_fields=["is_superuser"])
        check(100, {"fluvial", "coastal"})

    def test_adaptation_discovery_and_protected_features_exclude_restricted_hazards(self):
        Dataset.objects.create(
            id="coastal", label="Coastal", group="hazards", quantity="depth", unit="m",
            stacking_order=0, display_order=0,
        )
        for hazard in ("coastal", "flood"):
            AdaptationCostBenefit.objects.create(
                feature=self.features[0], hazard=hazard, protector_feature_id=123,
                parameter_set=ModelParameterSet.for_values("adaptation", {"gwl": 2}),
                adaptation_name="Wall", adaptation_protection_level=50, adaptation_cost=20,
            )
        response = self.client.get("/map/model-scenarios/adaptation", {"protector_id": 123})
        self.assertEqual([row["hazard"] for row in response.json()], ["flood"])
        response = self.client.get("/map/features/123/protected-by", {"parameters": json.dumps({"gwl": 2})})
        self.assertEqual([row["hazard"] for row in response.json()], ["flood"])
        query = {"layer": "roads", "field": "adaptation_cost", "dimensions": json.dumps({
            "hazard": "coastal", "parameters": {"gwl": 2}, "adaptation_name": "Wall",
            "adaptation_protection_level": 50,
        })}
        response = self.client.get("/map/features/sorted-by/adaptation", query)
        self.assertEqual(response.json()["items"], [])
        response = self.client.post(
            "/map/attributes/adaptation?" + urlencode(query),
            {"ids": [self.features[0].pk]}, format="json",
        )
        self.assertEqual(response.json()[str(self.features[0].pk)], None)

    def test_all_hazards_uses_one_exact_parameter_set_per_hazard(self):
        road, power = self.features
        self.damage(road, {"SLR": 20}, hazard="coastal", amount=100)
        self.damage(road, {"GWL": 2}, hazard="fluvial", amount=10)
        self.damage(road, {"GWL": 2}, hazard="pluvial", amount=5)
        self.damage(power, {"GWL": 2}, hazard="fluvial", amount=7)
        # These rows must not be counted: other scenarios, protection standards,
        # schemas, and hazards outside the selected combination.
        self.damage(road, {"SLR": 0}, hazard="coastal", amount=1000)
        self.damage(road, {"GWL": 3}, hazard="fluvial", amount=1000)
        self.damage(road, {"GWL": 2, "SLR": 20}, hazard="fluvial", amount=1000)
        self.damage(road, {"GWL": 2}, hazard="fluvial", protection=100, amount=1000)
        self.damage(road, {"GWL": 2}, hazard="wind", amount=1000)
        dimensions = {
            "hazard": "all", "parameters": {"SLR": 20, "GWL": 2}, "protection_standard": 0,
            "hazard_parameters": {"coastal": {"SLR": 20}, "fluvial": {"GWL": 2}, "pluvial": {"GWL": 2}},
        }

        def check(expected):
            query = {"layer": "roads", "field": "ead_mean", "dimensions": json.dumps(dimensions)}
            response = self.client.post(
                "/map/attributes/damages_expected?" + urlencode(query),
                {"ids": [road.pk, power.pk, 999999]}, format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {str(road.pk): expected, str(power.pk): None, "999999": None})
            response = self.client.get("/map/features/sorted-by/damages_expected", query)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["total"], 1)
            self.assertEqual(response.json()["items"][0]["value"], expected)

        check(115)
        Dataset.objects.create(
            id="coastal", label="Coastal", group="hazards", quantity="depth", unit="m",
            stacking_order=0, display_order=0,
        )
        check(15)  # Explicit hazard selections must still respect permissions.

    def test_all_hazard_parameter_mapping_must_match_the_combined_controls(self):
        self.damage(self.features[0], {"GWL": 2})
        base = {"hazard": "all", "parameters": {"GWL": 2}, "protection_standard": 0}
        for extra in (
            {"hazard_parameters": {}},
            {"hazard_parameters": {"flood": {"GWL": 3}}},
            {"hazard_parameters": {"flood": {"other": 2}}},
            {"hazard_parameters": {"all": {"GWL": 2}}},
            {"hazard_parameters": {"flood": {"GWL": 2}}, "hazard": "flood"},
        ):
            query = {"layer": "roads", "field": "ead_mean", "dimensions": json.dumps({**base, **extra})}
            with self.subTest(extra=extra):
                response = self.client.post(
                    "/map/attributes/damages_expected?" + urlencode(query),
                    {"ids": [self.features[0].pk]}, format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.client.get("/map/features/sorted-by/damages_expected", query).status_code, 400)
