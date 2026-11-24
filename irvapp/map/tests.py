import json
from importlib import import_module
from types import SimpleNamespace

from allauth.account.models import EmailAddress
from django.apps import apps
from django.contrib.auth.models import Group, User
from django.contrib.gis.geos import Point
from django.db import IntegrityError, connection, transaction
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import APIClient
from raster.models import RasterTileSource

from map.models import (
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesRp,
    Dataset,
    Feature,
    FeatureLayer,
    ModelParameterSet,
)
from map.model_parameters import canonical_parameter_key
from map.serializers import DatasetSerializer


def make_parameter_set(model_type, **values):
    return ModelParameterSet.for_values(model_type, values)


def grant_layer_access(user, layer):
    dataset = Dataset.objects.create(id=layer.pk, label=layer.pk, group="infrastructure")
    group = Group.objects.create(name=f"access-{layer.pk}")
    dataset.access_groups.add(group)
    user.groups.add(group)
    layer.identity.dataset = dataset
    layer.identity.save(update_fields=["dataset"])


class ModelParameterKeyTests(SimpleTestCase):
    def test_numeric_values_match_after_browser_round_trip(self):
        self.assertEqual(
            canonical_parameter_key({"gwl": 2.0, "slr": 0.5, "epoch": 2050}),
            canonical_parameter_key({"epoch": 2050.0, "slr": 0.5, "gwl": 2}),
        )

    def test_nested_values_are_normalized(self):
        self.assertEqual(
            canonical_parameter_key({"values": [2.0, {"slr": -0.0}]}),
            canonical_parameter_key({"values": [2, {"slr": 0}]}),
        )

    def test_strings_booleans_and_fractional_values_remain_distinct(self):
        keys = {
            canonical_parameter_key({"value": value})
            for value in (2, "2", True, 1, 0.5, None)
        }
        self.assertEqual(len(keys), 6)


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
        grant_layer_access(self.user, self.layer)
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

    def test_parameter_sets_reuse_equivalent_numeric_values(self):
        first = make_parameter_set("damages_expected", gwl=2.0, slr=0.5)
        second = make_parameter_set("damages_expected", slr=0.5, gwl=2)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.parameters.count(), 2)

    def test_result_ids_are_unique(self):
        cases = [
            (AdaptationCostBenefit, {"adaptation_name": "wall", "adaptation_protection_level": 1.0}),
            (DamagesExpected, {"protection_standard": 0}),
            (DamagesRp, {"rp": 100}),
        ]
        for model, dimensions in cases:
            with self.subTest(model=model.__name__):
                values = {
                    "feature": self.feature_1,
                    "parameter_set": make_parameter_set(model._meta.db_table, gwl=2),
                    **dimensions,
                }
                result = model.objects.create(hazard="flood", **values)
                self.assertIsNotNone(result.id)
                with self.assertRaises(IntegrityError), transaction.atomic():
                    model.objects.create(id=result.id, hazard="storm", **values)

    def test_parameter_key_migration_merges_nonoverlapping_results(self):
        legacy = ModelParameterSet.objects.create(
            model_type="damages_expected", canonical_key='{"gwl":2.0}'
        )
        legacy.parameters.create(name="gwl", value=2.0)
        retained = make_parameter_set("damages_expected", gwl=2)
        result = DamagesExpected.objects.create(
            feature=self.feature_1, parameter_set=legacy,
            hazard="flood", protection_standard=0, ead_mean=10,
        )
        DamagesExpected.objects.create(
            feature=self.feature_1, parameter_set=retained,
            hazard="storm", protection_standard=0, ead_mean=20,
        )
        migration = import_module("map.migrations.0020_normalize_parameter_keys")
        migration.normalize_parameter_keys(apps, SimpleNamespace(connection=connection))
        # Reassignment changes the composite primary key; the public ID stays stable.
        result = DamagesExpected.objects.get(id=result.id)
        self.assertEqual(result.parameter_set_id, retained.pk)
        self.assertEqual(result.ead_mean, 10)
        self.assertFalse(ModelParameterSet.objects.filter(pk=legacy.pk).exists())
        self.assertEqual(DamagesExpected.objects.count(), 2)

    def test_parameter_key_migration_normalizes_a_single_legacy_set(self):
        legacy = ModelParameterSet.objects.create(
            model_type="damages_expected", canonical_key='{"gwl":2.0}'
        )
        legacy.parameters.create(name="gwl", value=2.0)
        migration = import_module("map.migrations.0020_normalize_parameter_keys")
        migration.normalize_parameter_keys(apps, SimpleNamespace(connection=connection))
        self.assertEqual(make_parameter_set("damages_expected", gwl=2).pk, legacy.pk)

    def test_parameter_key_migration_preserves_overlapping_results(self):
        legacy = ModelParameterSet.objects.create(
            model_type="damages_expected", canonical_key='{"gwl":2.0}'
        )
        legacy.parameters.create(name="gwl", value=2.0)
        retained = make_parameter_set("damages_expected", gwl=2)
        for parameter_set, damage in ((legacy, 10), (retained, 20)):
            DamagesExpected.objects.create(
                feature=self.feature_1, parameter_set=parameter_set,
                hazard="flood", protection_standard=0, ead_mean=damage,
            )
        migration = import_module("map.migrations.0020_normalize_parameter_keys")
        with self.assertRaisesMessage(RuntimeError, "overlapping"), transaction.atomic():
            migration.normalize_parameter_keys(apps, SimpleNamespace(connection=connection))
        self.assertEqual(ModelParameterSet.objects.count(), 2)
        self.assertEqual(
            list(DamagesExpected.objects.order_by("ead_mean").values_list("ead_mean", flat=True)),
            [10, 20],
        )

    def test_damages_expected_lookup_with_hazard_all_aggregates(self):
        DamagesExpected.objects.create(
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_1,
            hazard="flood",
            protection_standard=100,
            ead_mean=10.0,
        )
        DamagesExpected.objects.create(
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_1,
            hazard="storm",
            protection_standard=100,
            ead_mean=5.0,
        )
        DamagesExpected.objects.create(
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_2,
            hazard="flood",
            protection_standard=100,
            ead_mean=7.0,
        )

        response = self.client.post(
            "/map/attributes/damages_expected",
            data={"ids": [self.feature_1.id, self.feature_2.id, 999999]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=ead_mean"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "all",
                        "parameters": {"rcp": "8.5", "epoch": 2050},
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
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_1,
            hazard="flood",
            protection_standard=100,
            ead_mean=10.0,
        )

        response = self.client.post(
            "/map/attributes/damages_expected",
            data=[self.feature_1.id],
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=ead_mean"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "parameters": {"rcp": "8.5", "epoch": 2050},
                        "protection_standard": 100,
                    }
                )
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[str(self.feature_1.id)], 10.0)

    def test_damages_expected_lookup_accepts_gwl_and_slr_parameters(self):
        DamagesExpected.objects.create(
            feature=self.feature_1,
            hazard="flood",
            parameter_set=make_parameter_set(
                "damages_expected", gwl=2.0, slr=0.5
            ),
            protection_standard=100,
            ead_mean=12.0,
        )

        response = self.client.post(
            "/map/attributes/damages_expected",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads&field=ead_mean&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "parameters": {"gwl": 2, "slr": 0.5},
                        "protection_standard": 100,
                    }
                )
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[str(self.feature_1.id)], 12.0)

        response = self.client.get(
            "/map/features/sorted-by/damages_expected",
            {
                "layer": "roads",
                "field": "ead_mean",
                "dimensions": json.dumps({
                    "hazard": "flood",
                    "parameters": {"gwl": 2, "slr": 0.5},
                    "protection_standard": 100,
                }),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["value"], 12.0)

    def test_protected_features_match_equivalent_numeric_parameters(self):
        AdaptationCostBenefit.objects.create(
            parameter_set=make_parameter_set("adaptation", gwl=2.0),
            feature=self.feature_1,
            hazard="flood",
            adaptation_name="wall",
            adaptation_protection_level=1.0,
            protector_feature_id=123,
        )
        response = self.client.get(
            "/map/features/123/protected-by",
            {"parameters": json.dumps({"gwl": 2})},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], self.feature_1.id)

    def test_adaptation_lookup_cost_benefit_ratio(self):
        AdaptationCostBenefit.objects.create(
            parameter_set=make_parameter_set("adaptation", rcp='8.5'),
            feature=self.feature_1,
            hazard="flood",
            adaptation_name="wall",
            adaptation_protection_level=1.0,
            adaptation_cost=20.0,
            avoided_ead_mean=10.0,
            avoided_eael_mean=15.0,
        )

        response = self.client.post(
            "/map/attributes/adaptation",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=cost_benefit_ratio"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "parameters": {"rcp": "8.5"},
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
            "/map/attributes/not-a-group",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=ead_mean"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "parameters": {"rcp": "8.5", "epoch": 2050},
                        "protection_standard": 100,
                    }
                )
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("field_group", response.json())

    def test_returns_400_for_invalid_parameters_json(self):
        response = self.client.post(
            "/map/attributes/adaptation",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=cost_benefit_ratio"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "parameters": {"rcp": "8.5"},
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
            "/map/attributes/damages_expected",
            data={"ids": [self.feature_1.id]},
            format="json",
            QUERY_STRING=(
                "layer=roads"
                "&field=not_a_real_field"
                "&dimensions="
                + json.dumps(
                    {
                        "hazard": "flood",
                        "parameters": {"rcp": "8.5", "epoch": 2050},
                        "protection_standard": 100,
                    }
                )
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("field", response.json())


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="testuser@example.com",
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=True,
        )

    def test_current_user_returns_anonymous_and_sets_csrf_cookie(self):
        response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"authenticated": False, "user": None},
        )
        self.assertIn("csrftoken", response.cookies)

    def test_login_then_current_user_returns_authenticated_user(self):
        self.client.get("/auth/me")
        csrf_token = self.client.cookies["csrftoken"].value

        login_response = self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["authenticated"], True)
        self.assertEqual(
            login_response.json()["user"]["username"],
            "testuser",
        )

        current_user_response = self.client.get("/auth/me")
        self.assertEqual(current_user_response.status_code, 200)
        self.assertEqual(current_user_response.json()["authenticated"], True)
        self.assertEqual(
            current_user_response.json()["user"]["username"],
            "testuser",
        )

    def test_login_rejects_invalid_credentials(self):
        self.client.get("/auth/me")
        csrf_token = self.client.cookies["csrftoken"].value

        response = self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"],
            "Invalid username or password.",
        )

    def test_logout_clears_authenticated_session(self):
        self.client.get("/auth/me")
        csrf_token = self.client.cookies["csrftoken"].value

        self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        # Django rotates the CSRF token on login; use the fresh token.
        csrf_token = self.client.cookies["csrftoken"].value

        logout_response = self.client.post(
            "/auth/logout",
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(
            logout_response.json(),
            {"authenticated": False, "user": None},
        )

        current_user_response = self.client.get("/auth/me")
        self.assertEqual(current_user_response.status_code, 200)
        self.assertEqual(
            current_user_response.json(),
            {"authenticated": False, "user": None},
        )


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
        grant_layer_access(self.user, self.layer)
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
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_1,
            hazard="flood",
            protection_standard=100,
            ead_mean=10.0,
        )
        DamagesExpected.objects.create(
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_1,
            hazard="storm",
            protection_standard=100,
            ead_mean=5.0,
        )
        DamagesExpected.objects.create(
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_2,
            hazard="flood",
            protection_standard=100,
            ead_mean=7.0,
        )

        response = self.client.get(
            "/map/features/sorted-by/damages_expected",
            {
                "layer": "roads",
                "field": "ead_mean",
                "page": 1,
                "size": 1,
                "dimensions": json.dumps(
                    {
                        "hazard": "all",
                        "parameters": {"rcp": "8.5", "epoch": 2050},
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
            parameter_set=make_parameter_set("adaptation", rcp='8.5'),
            feature=self.feature_1,
            hazard="flood",
            adaptation_name="wall",
            adaptation_protection_level=1.0,
            protector_feature_id=123,
            adaptation_cost=20.0,
            avoided_ead_mean=10.0,
            avoided_eael_mean=15.0,
        )

        response = self.client.get(
            "/map/features/123/protected-by",
            {"parameters": json.dumps({"rcp": "8.5"})},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], self.feature_1.id)
        self.assertEqual(response.json()[0]["string_id"], "road-1")
        self.assertEqual(response.json()[0]["adaptation_name"], "wall")
        self.assertEqual(response.json()[0]["parameters"]["rcp"], "8.5")

    def test_feature_detail_route_returns_related_records(self):
        AdaptationCostBenefit.objects.create(
            parameter_set=make_parameter_set("adaptation", rcp='8.5'),
            feature=self.feature_1,
            hazard="flood",
            adaptation_name="wall",
            adaptation_protection_level=1.0,
            adaptation_cost=20.0,
            avoided_ead_mean=10.0,
            avoided_eael_mean=15.0,
        )
        DamagesExpected.objects.create(
            parameter_set=make_parameter_set("damages_expected", rcp='8.5', epoch=2050),
            feature=self.feature_1,
            hazard="flood",
            protection_standard=100,
            ead_mean=10.0,
        )
        DamagesRp.objects.create(
            parameter_set=make_parameter_set("damages_rp", rcp='8.5', epoch=2050),
            feature=self.feature_1,
            hazard="flood",
            rp=100,
            damage_mean=2.5,
        )

        response = self.client.get(f"/map/features/{self.feature_1.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], self.feature_1.id)
        self.assertEqual(payload["string_id"], "road-1")
        self.assertEqual(len(payload["adaptation"]), 1)
        self.assertEqual(payload["adaptation"][0]["adaptation_name"], "wall")
        self.assertEqual(len(payload["damages_expected"]), 1)
        self.assertEqual(payload["damages_expected"][0]["parameters"]["epoch"], 2050)
        self.assertEqual(len(payload["damages_return_period"]), 1)
        self.assertEqual(payload["damages_return_period"][0]["rp"], 100)
        self.assertNotIn("damages_npv", payload)


class DatasetRouteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        self.access_group = Group.objects.create(name="dataset-access")
        self.user.groups.add(self.access_group)
        self.client.force_authenticate(user=self.user)
        self.tile_source = RasterTileSource.objects.create(
            keys=["type", "epoch"],
        )
        datasets = [
            Dataset.objects.create(
                id="flood_extent",
                label="Flood extent",
                group="hazards",
            ),
            Dataset.objects.create(
                id="storm_track",
                label="Storm track",
                group="hazards",
                license="CC-BY",
            ),
            Dataset.objects.create(
                id="roads",
                label="Road network",
                group="networks",
            ),
        ]
        for dataset in datasets:
            dataset.access_groups.add(self.access_group)

    def test_datasets_route_returns_all_datasets_without_group_filter(self):
        response = self.client.get("/map/datasets")

        self.assertEqual(response.status_code, 200)
        payload = response.json()["results"]
        self.assertEqual(len(payload), 3)

    def test_datasets_route_returns_license(self):
        response = self.client.get("/map/datasets/storm_track")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["license"], "CC-BY")
        self.assertNotIn("quantity", response.json())
        self.assertNotIn("unit", response.json())

    def test_datasets_route_filters_by_group(self):
        response = self.client.get("/map/datasets", {"group": "hazards"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()["results"]
        self.assertEqual(len(payload), 2)
        self.assertEqual(
            sorted(item["id"] for item in payload),
            ["flood_extent", "storm_track"],
        )

    def test_datasets_route_filters_by_group_case_insensitive(self):
        response = self.client.get("/map/datasets", {"group": "HAZARDS"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 2)

    def test_datasets_route_marks_restricted_datasets(self):
        access_group = Group.objects.create(name="hazard-data")
        restricted = Dataset.objects.get(pk="storm_track")
        restricted.access_groups.clear()
        restricted.access_groups.add(access_group)

        response = self.client.get("/map/datasets")

        self.assertEqual(response.status_code, 200)
        payload = {
            item["id"]: item for item in response.json()["results"]
        }
        self.assertEqual(
            set(payload), {"flood_extent", "storm_track", "roads"})
        self.assertTrue(payload["flood_extent"]["has_access"])
        self.assertFalse(payload["storm_track"]["has_access"])
        self.assertNotIn("access_groups", payload["storm_track"])

    def test_group_member_can_list_and_retrieve_restricted_dataset(self):
        access_group = Group.objects.create(name="hazard-data")
        restricted = Dataset.objects.get(pk="storm_track")
        restricted.access_groups.clear()
        restricted.access_groups.add(access_group)
        self.user.groups.add(access_group)

        list_response = self.client.get("/map/datasets")
        detail_response = self.client.get("/map/datasets/storm_track")

        self.assertEqual(len(list_response.json()["results"]), 3)
        storm_track = next(
            item
            for item in list_response.json()["results"]
            if item["id"] == "storm_track"
        )
        self.assertTrue(storm_track["has_access"])
        self.assertEqual(detail_response.status_code, 200)

    def test_restricted_dataset_detail_returns_forbidden(self):
        access_group = Group.objects.create(name="hazard-data")
        restricted = Dataset.objects.get(pk="storm_track")
        restricted.access_groups.clear()
        restricted.access_groups.add(access_group)

        response = self.client.get("/map/datasets/storm_track")

        self.assertEqual(response.status_code, 403)

    def test_dataset_without_access_groups_is_denied(self):
        dataset = Dataset.objects.get(pk="roads")
        dataset.access_groups.clear()

        list_response = self.client.get("/map/datasets")
        detail_response = self.client.get("/map/datasets/roads")

        roads = next(
            item
            for item in list_response.json()["results"]
            if item["id"] == "roads"
        )
        self.assertFalse(roads["has_access"])
        self.assertEqual(detail_response.status_code, 403)

    def test_dataset_serializer_supports_dict_rows(self):
        dataset = Dataset.objects.get(pk="storm_track")
        request = APIRequestFactory().get("/map/datasets")
        request.user = self.user

        serializer = DatasetSerializer(
            dataset.__class__.objects.values().get(pk=dataset.pk),
            context={"request": request},
        )

        self.assertTrue(serializer.data["has_access"])
