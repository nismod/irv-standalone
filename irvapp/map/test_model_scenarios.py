from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from map.models import (
    AdaptationCostBenefit, DamagesExpected, Feature, FeatureLayer, ModelParameterSet,
)


class ModelScenarioTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user(username="scenarios"))
        self.features = []
        for name, sector in (("roads", "transport"), ("power", "energy")):
            layer = FeatureLayer.objects.create(
                layer_name=name, sector=sector, subsector=name, asset_type="edge",
            )
            self.features.append(Feature.objects.create(
                layer=layer, string_id=name, properties={}, geom=Point(0, 0, srid=4326),
            ))

    def damage(self, feature, parameters, hazard="flood", protection=0):
        return DamagesExpected.objects.create(
            feature=feature, hazard=hazard, protection_standard=protection,
            parameter_set=ModelParameterSet.for_values("damages_expected", parameters),
            ead_mean=10,
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
