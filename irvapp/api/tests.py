import json

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesRp,
    Feature,
    FeatureLayer,
)


class AttributeLookupViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.force_authenticate(user=self.user)
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
            "/attributes/damages_expected",
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

    def test_damages_expected_lookup_accepts_list_body(self):
        DamagesExpected.objects.create(
            feature=self.feature_1,
            hazard="flood",
            rcp="8.5",
            epoch=2050,
            protection_standard=100,
            ead_mean=10.0,
        )

        response = self.client.post(
            "/attributes/damages_expected",
            data=[self.feature_1.id],
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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[str(self.feature_1.id)], 10.0)

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
            "/attributes/adaptation",
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
            "/attributes/not-a-group",
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
            "/attributes/adaptation",
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
            "/attributes/damages_expected",
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


class FeatureRouteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.force_authenticate(user=self.user)
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

    def test_sorted_features_returns_fastapi_style_page(self):
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

        response = self.client.get(
            "/features/sorted-by/damages_expected",
            {
                "layer": "roads",
                "field": "ead_mean",
                "page": 1,
                "size": 1,
                "dimensions": json.dumps(
                    {
                        "hazard": "all",
                        "rcp": "8.5",
                        "epoch": 2050,
                        "protection_standard": 100,
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 2)
        self.assertEqual(response.json()["page"], 1)
        self.assertEqual(response.json()["size"], 1)
        self.assertEqual(response.json()["pages"], 2)
        self.assertEqual(response.json()["items"][0]["id"], self.feature_1.id)
        self.assertEqual(response.json()["items"][0]["value"], 15.0)

    def test_protected_features_returns_adaptation_options(self):
        AdaptationCostBenefit.objects.create(
            feature=self.feature_1,
            hazard="flood",
            rcp="8.5",
            adaptation_name="wall",
            adaptation_protection_level=1.0,
            protector_feature_id=123,
            adaptation_cost=20.0,
            avoided_ead_mean=10.0,
            avoided_eael_mean=15.0,
        )

        response = self.client.get(
            "/features/123/protected-by",
            {"rcp": "8.5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], self.feature_1.id)
        self.assertEqual(response.json()[0]["string_id"], "road-1")
        self.assertEqual(response.json()[0]["adaptation_name"], "wall")
        self.assertEqual(response.json()[0]["rcp"], "8.5")

    def test_feature_detail_route_returns_related_records(self):
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
        DamagesExpected.objects.create(
            feature=self.feature_1,
            hazard="flood",
            rcp="8.5",
            epoch=2050,
            protection_standard=100,
            ead_mean=10.0,
        )
        DamagesRp.objects.create(
            feature=self.feature_1,
            hazard="flood",
            rcp="8.5",
            epoch=2050,
            rp=100,
            damage_mean=2.5,
        )

        response = self.client.get(f"/features/{self.feature_1.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], self.feature_1.id)
        self.assertEqual(payload["string_id"], "road-1")
        self.assertEqual(len(payload["adaptation"]), 1)
        self.assertEqual(payload["adaptation"][0]["adaptation_name"], "wall")
        self.assertEqual(len(payload["damages_expected"]), 1)
        self.assertEqual(payload["damages_expected"][0]["epoch"], 2050)
        self.assertEqual(len(payload["damages_return_period"]), 1)
        self.assertEqual(payload["damages_return_period"][0]["rp"], 100)
        self.assertEqual(payload["damages_npv"], [])
