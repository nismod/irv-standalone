import json

from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (
    AdaptationCostBenefit,
    DamagesExpected,
    Feature,
    FeatureLayer,
)


class AttributeLookupViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.layer = FeatureLayer.objects.create(
            layer_name="roads",
            sector="transport",
            subsector="road",
            asset_type="edge",
        )
        self.feature_1 = Feature.objects.create(
            string_id="road-1",
            layer=self.layer,
            properties={"name": "A"},
            geom=Point(0.0, 0.0, srid=4326),
        )
        self.feature_2 = Feature.objects.create(
            string_id="road-2",
            layer=self.layer,
            properties={"name": "B"},
            geom=Point(1.0, 1.0, srid=4326),
        )

    def test_damages_expected_lookup_with_hazard_all_aggregates(self):
        DamagesExpected.objects.create(
            feature=self.feature_1,
            hazard="flood",
            rcp="8.5",
            epoch=2050,
            protection_standard=100,
            ead_mean=10.0,
        )
        DamagesExpected.objects.create(
            feature=self.feature_1,
            hazard="storm",
            rcp="8.5",
            epoch=2050,
            protection_standard=100,
            ead_mean=5.0,
        )
        DamagesExpected.objects.create(
            feature=self.feature_2,
            hazard="flood",
            rcp="8.5",
            epoch=2050,
            protection_standard=100,
            ead_mean=7.0,
        )

        response = self.client.post(
            "/api/attributes/damages_expected/",
            data={"ids": [self.feature_1.id, self.feature_2.id, 999999]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=ead_mean"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "all",
                        "rcp": "8.5",
                        "epoch": 2050,
                        "protection_standard": 100,
                    }
                )
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[str(self.feature_1.id)], 15.0)
        self.assertEqual(response.json()[str(self.feature_2.id)], 7.0)
        self.assertIsNone(response.json()["999999"])

    def test_adaptation_lookup_cost_benefit_ratio(self):
        AdaptationCostBenefit.objects.create(
            feature=self.feature_1,
            hazard="flood",
            rcp="8.5",
            adaptation_name="wall",
            adaptation_protection_level=1.0,
            adaptation_cost=20.0,
            avoided_ead_mean=10.0,
            avoided_eael_mean=15.0,
        )

        response = self.client.post(
            "/api/attributes/adaptation/",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=cost_benefit_ratio"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "rcp": "8.5",
                        "adaptation_name": "wall",
                        "adaptation_protection_level": 1.0,
                    }
                )
                + "&parameters="
                + json.dumps({"eael_days": 15})
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[str(self.feature_1.id)], 1.25)

    def test_returns_400_for_invalid_field_group(self):
        response = self.client.post(
            "/api/attributes/not-a-group/",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=ead_mean"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "rcp": "8.5",
                        "epoch": 2050,
                        "protection_standard": 100,
                    }
                )
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("field_group", response.json())

    def test_returns_400_for_invalid_parameters_json(self):
        response = self.client.post(
            "/api/attributes/adaptation/",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=cost_benefit_ratio"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "rcp": "8.5",
                        "adaptation_name": "wall",
                        "adaptation_protection_level": 1.0,
                    }
                )
                + "&parameters={not-json"
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("parameters", response.json())

    def test_returns_400_for_invalid_field_name(self):
        response = self.client.post(
            "/api/attributes/damages_expected/",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=not_a_real_field"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "rcp": "8.5",
                        "epoch": 2050,
                        "protection_standard": 100,
                    }
                )
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("field", response.json())
