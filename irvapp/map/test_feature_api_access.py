import json

from django.contrib.auth.models import Group, User
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIClient

from map.models import (
    AdaptationCostBenefit, DamagesExpected, DamagesRp, Dataset, Feature,
    FeatureLayer, LayerIdentity, ModelParameterSet, RasterLayer,
)
from raster.models import RasterTileSource


class FeatureAPIAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="feature-api")
        self.group = Group.objects.create(name="allowed")
        self.user.groups.add(self.group)
        allowed = Dataset.objects.create(id="allowed", label="Allowed", group="infrastructure")
        allowed.access_groups.add(self.group)
        restricted = Dataset.objects.create(id="restricted", label="Restricted", group="infrastructure")
        restricted.access_groups.add(Group.objects.create(name="other"))
        self.features = {}
        self.damages = {}
        self.adaptations = {}
        self.rp = {}
        for name, dataset in (("allowed", allowed), ("restricted", restricted), ("unlinked", None)):
            LayerIdentity.objects.create(id=name, kind="feature", dataset=dataset)
            layer = FeatureLayer.objects.create(
                layer_name=name, sector="transport", subsector="road", asset_type="edge",
            )
            feature = Feature.objects.create(
                string_id=name, layer=layer, properties={"name": name}, geom=Point(0, 0, srid=4326),
            )
            self.features[name] = feature
            params = {"scenario": name}
            self.damages[name] = DamagesExpected.objects.create(
                feature=feature, hazard="flood", protection_standard=0, ead_mean=10,
                parameter_set=ModelParameterSet.for_values("damages_expected", params),
            )
            self.rp[name] = DamagesRp.objects.create(
                feature=feature, hazard="flood", rp=100,
                parameter_set=ModelParameterSet.for_values("damages_rp", params),
            )
            self.adaptations[name] = AdaptationCostBenefit.objects.create(
                feature=feature, hazard="flood", adaptation_name="wall", adaptation_protection_level=1,
                protector_feature_id=123, adaptation_cost=5,
                parameter_set=ModelParameterSet.for_values("adaptation", params),
            )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_feature_and_result_lists_and_details_are_filtered(self):
        for endpoint, objects in (
            ("features", self.features), ("damages-expected", self.damages),
            ("damages-rp", self.rp), ("adaptation-cost-benefits", self.adaptations),
        ):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(f"/map/{endpoint}")
                self.assertEqual([row["id"] for row in response.json()["results"]], [objects["allowed"].id])
                for name in ("restricted", "unlinked"):
                    self.assertEqual(self.client.get(f"/map/{endpoint}/{objects[name].id}").status_code, 404)
                self.assertEqual(self.client.get(f"/map/{endpoint}/{objects['allowed'].id}").status_code, 200)
        self.user.groups.remove(self.group)
        self.assertEqual(self.client.get("/map/features").json()["results"], [])
        self.user.groups.add(self.group)
        self.assertEqual(len(self.client.get("/map/features").json()["results"]), 1)

    def test_lookups_and_scenarios_exclude_other_layers(self):
        rows = self.client.get("/map/model-scenarios/damages_expected").json()
        self.assertEqual([row["parameters"] for row in rows], [{"scenario": "allowed"}])
        rows = self.client.get("/map/model-scenarios/damages_expected", {"layer": "restricted"}).json()
        self.assertEqual(rows, [])
        params = {"scenario": "restricted"}
        dimensions = {"hazard": "flood", "parameters": params, "protection_standard": 0}
        query = {"layer": "restricted", "field": "ead_mean", "dimensions": json.dumps(dimensions)}
        sorted_response = self.client.get("/map/features/sorted-by/damages_expected", query)
        self.assertEqual(sorted_response.json()["items"], [])
        lookup = self.client.post("/map/attributes/damages_expected", {"ids": [self.features['restricted'].id]}, format="json", QUERY_STRING=(
            "layer=restricted&field=ead_mean&dimensions=" + json.dumps(dimensions)
        ))
        self.assertIsNone(lookup.json()[str(self.features['restricted'].id)])
        response = self.client.get("/map/features/123/protected-by", {"parameters": json.dumps(params)})
        self.assertEqual(response.json(), [])
        self.assertEqual(self.client.get("/map/model-scenarios/adaptation", {"protector_id": 123}).json()[0]["parameters"], {"scenario": "allowed"})

    def test_feature_detail_and_results_hide_restricted_hazards(self):
        hazard = Dataset.objects.create(id="secret", label="Secret", group="hazards")
        hazard.access_groups.add(Group.objects.create(name="hazard-other"))
        secret = DamagesExpected.objects.create(
            feature=self.features['allowed'], hazard="secret", protection_standard=0,
            parameter_set=ModelParameterSet.for_values("damages_expected", {"scenario": "secret"}),
        )
        detail = self.client.get(f"/map/features/{self.features['allowed'].id}").json()
        self.assertEqual([row['id'] for row in detail['damages_expected']], [self.damages['allowed'].id])
        self.assertEqual(self.client.get(f"/map/damages-expected/{secret.id}").status_code, 404)
        self.assertNotIn("secret", [row['hazard'] for row in self.client.get('/map/damages-expected').json()['results']])

    def test_anonymous_requests_are_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/map/features').status_code, 403)

    def test_hazard_dataset_id_is_restricted_even_when_layer_id_differs(self):
        dataset = Dataset.objects.create(id='coastal', label='Coastal', group='hazards')
        group = Group.objects.create(name='coastal-access')
        dataset.access_groups.add(group)
        source = RasterTileSource.objects.create(keys=['type'])
        LayerIdentity.objects.create(id='coast-v2', kind='raster', dataset=dataset)
        RasterLayer.objects.create(id='coast-v2', tile_source=source,
            label='Coast', quantity='depth', unit='m', stacking_order=0, display_order=0)
        params = {'scenario': 'coastal-only'}
        result = DamagesExpected.objects.create(
            feature=self.features['allowed'], hazard='coastal', protection_standard=0, ead_mean=7,
            parameter_set=ModelParameterSet.for_values('damages_expected', params),
        )
        adaptation = AdaptationCostBenefit.objects.create(
            feature=self.features['allowed'], hazard='coastal', protector_feature_id=123,
            adaptation_name='wall', adaptation_protection_level=1,
            parameter_set=ModelParameterSet.for_values('adaptation', params),
        )
        dimensions = {'hazard': 'coastal', 'parameters': params, 'protection_standard': 0}
        query = {'layer': 'allowed', 'field': 'ead_mean', 'dimensions': json.dumps(dimensions)}
        self.assertEqual(self.client.get(f'/map/damages-expected/{result.id}').status_code, 404)
        self.assertEqual(self.client.get(f'/map/adaptation-cost-benefits/{adaptation.id}').status_code, 404)
        self.assertNotIn('coastal', [row['hazard'] for row in self.client.get('/map/model-scenarios/damages_expected').json()])
        self.assertEqual(self.client.get('/map/model-scenarios/adaptation', {'protector_id': 123, 'hazard': 'coastal'}).json(), [])
        self.assertEqual(self.client.get('/map/features/123/protected-by', {'parameters': json.dumps(params)}).json(), [])
        self.assertEqual(self.client.get('/map/features/sorted-by/damages_expected', query).json()['items'], [])
        response = self.client.post('/map/attributes/damages_expected', {'ids': [self.features['allowed'].id]},
            format='json', QUERY_STRING='layer=allowed&field=ead_mean&dimensions=' + json.dumps(dimensions))
        self.assertIsNone(response.json()[str(self.features['allowed'].id)])
        self.user.groups.add(group)
        self.assertEqual(self.client.get(f'/map/damages-expected/{result.id}').status_code, 200)
        self.assertEqual(self.client.get(f'/map/adaptation-cost-benefits/{adaptation.id}').status_code, 200)
