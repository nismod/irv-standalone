from io import StringIO
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from map.management.commands.seed_synthetic_results import Command, RESULT_MODELS
from map.models import (
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesRp,
    Dataset,
    Feature,
    FeatureLayer,
    ModelParameter,
    ModelParameterSet,
    SyntheticDataRun,
)
from raster.models import RasterTileSource


@override_settings(DEBUG=True)
class SyntheticResultsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        roads = FeatureLayer.objects.create(
            layer_name="roads", sector="transport", subsector="road", asset_type="edge"
        )
        power = FeatureLayer.objects.create(
            layer_name="power",
            sector="power",
            subsector="transmission",
            asset_type="pole",
        )
        cls.features = [
            Feature.objects.create(
                layer=roads,
                string_id=f"road-{index}",
                properties={},
                geom=Point(57 + index / 100, -20, srid=4326),
            )
            for index in range(12)
        ]
        cls.other_feature = Feature.objects.create(
            layer=power,
            string_id="pole-1",
            properties={},
            geom=Point(57, -20, srid=4326),
        )
        for hazard, keys in (("fluvial", ["GWL", "RP"]), ("coastal", ["SLR", "RP"])):
            source = RasterTileSource.objects.create(
                keys=keys, database=hazard + ".sqlite"
            )
            Dataset.objects.create(
                id=hazard,
                label=hazard.title(),
                group="hazards",
                quantity="depth",
                unit="m",
                tile_source=source,
                stacking_order=0,
                display_order=0,
            )

    def setUp(self):
        domains = {
            "fluvial.sqlite": [
                {"GWL": "0.75", "RP": "20"},
                {"GWL": "0.75", "RP": "100"},
                {"GWL": "2", "RP": "100"},
                {"GWL": "2", "RP": "500"},
            ],
            "coastal.sqlite": [{"SLR": "0", "RP": "100"}, {"SLR": "20", "RP": "100"}],
        }
        patcher = patch(
            "map.management.commands.seed_synthetic_results._source_options",
            side_effect=lambda database, filters=None: domains[database],
        )
        self.source_options = patcher.start()
        self.addCleanup(patcher.stop)

    def seed(self, *args):
        output = StringIO()
        call_command(
            "seed_synthetic_results",
            "--layer",
            "roads",
            *([] if "--all-features" in args else ["--limit-per-layer", "12"]),
            *args,
            stdout=output,
        )
        return output.getvalue()

    def snapshot(self):
        return {
            key: list(
                model.objects.order_by("pk").values(
                    *[
                        field.name
                        for field in model._meta.fields
                        if field.name not in ("pk", "id", "parameter_set")
                    ],
                    "parameter_set__canonical_key",
                )
            )
            for key, model in RESULT_MODELS.items()
        }

    def test_dry_run_does_not_create_results_parameter_sets_or_run(self):
        output = self.seed("--dry-run")
        self.assertIn("Dry run: no database changes.", output)
        self.assertIn('"GWL":0.75', output)
        for model in (
            *RESULT_MODELS.values(),
            ModelParameterSet,
            ModelParameter,
            SyntheticDataRun,
        ):
            self.assertEqual(model.objects.count(), 0)

    def test_generates_complete_sparse_raster_scenarios_and_consistent_values(self):
        with patch("map.management.commands.seed_synthetic_results.BATCH_SIZE", 7):
            self.seed()
        expected_counts = {
            "damages_expected": 96,
            "damages_rp": 72,
            "damages_npv": 48,
            "adaptation": 144,
        }
        run = SyntheticDataRun.objects.get()
        for key, model in RESULT_MODELS.items():
            self.assertEqual(model.objects.count(), expected_counts[key])
            self.assertEqual(len(run.result_ids[key]), expected_counts[key])
            self.assertEqual(
                set(run.result_ids[key]),
                set(model.objects.values_list("id", flat=True)),
            )
        self.assertEqual(
            {item.canonical_key for item in ModelParameterSet.objects.all()},
            {
                '{"GWL":0.75}',
                '{"GWL":2}',
                '{"SLR":0}',
                '{"SLR":20}',
            },
        )
        self.assertFalse(
            DamagesRp.objects.filter(
                parameter_set__canonical_key='{"GWL":0.75}', rp=500
            ).exists()
        )
        self.assertEqual(
            set(
                AdaptationCostBenefit.objects.values_list(
                    "protector_feature_id", flat=True
                )
            ),
            {self.features[0].id},
        )
        self.assertFalse(
            DamagesExpected.objects.filter(feature=self.other_feature).exists()
        )
        self.assertTrue(DamagesExpected.objects.filter(ead_mean=0).exists())
        self.assertTrue(DamagesExpected.objects.filter(ead_mean__isnull=True).exists())
        for row in DamagesExpected.objects.exclude(ead_mean__isnull=True):
            self.assertLessEqual(row.ead_amin, row.ead_mean)
            self.assertLessEqual(row.ead_mean, row.ead_amax)
        self.assertFalse(
            AdaptationCostBenefit.objects.filter(adaptation_cost__lte=0).exists()
        )

    def test_normalises_legacy_values_and_deduplicates_raster_confidence_rows(self):
        source = Dataset.objects.get(pk="fluvial").tile_source
        source.keys = ["type", "rp", "rcp", "epoch", "confidence"]
        source.save(update_fields=["keys"])
        self.source_options.side_effect = lambda *args, **kwargs: [
            {
                "type": "fluvial",
                "rp": "100",
                "rcp": "4x5",
                "epoch": "2050",
                "confidence": confidence,
            }
            for confidence in ("5", "95")
        ]
        self.seed("--hazard", "fluvial", "--limit-per-layer", "1")
        self.source_options.assert_called_once_with(
            "fluvial.sqlite", filters={"type": "fluvial"}
        )
        self.assertEqual(DamagesRp.objects.count(), 1)
        for parameters in ModelParameterSet.objects.all():
            self.assertEqual(parameters.values, {"rcp": "4.5", "epoch": 2050})

    def test_repeat_is_noop_and_clear_then_reseed_reproduces_values(self):
        self.seed()
        first = self.snapshot()
        self.assertIn("already exists; nothing changed", self.seed())
        self.assertEqual(first, self.snapshot())
        with self.assertRaisesMessage(CommandError, "different options"):
            self.seed("--seed", "7")
        self.seed("--clear", "--dry-run")
        self.assertEqual(first, self.snapshot())
        self.seed("--clear")
        for model in (
            *RESULT_MODELS.values(),
            ModelParameterSet,
            ModelParameter,
            SyntheticDataRun,
        ):
            self.assertEqual(model.objects.count(), 0)
        self.assertEqual(Feature.objects.count(), 13)
        self.assertEqual(Dataset.objects.count(), 2)
        self.seed()
        self.assertEqual(first, self.snapshot())

    def test_preserves_existing_results_and_shared_parameters_on_cleanup(self):
        existing_parameters = ModelParameterSet.for_values(
            "damages_expected", {"GWL": 0.75}
        )
        imported = DamagesExpected.objects.create(
            parameter_set=existing_parameters,
            feature=self.features[0],
            hazard="fluvial",
            protection_standard=0,
            ead_mean=777,
        )
        self.seed()
        imported.refresh_from_db()
        self.assertEqual(imported.ead_mean, 777)
        self.assertNotIn(
            imported.id, SyntheticDataRun.objects.get().result_ids["damages_expected"]
        )
        generated_parameters = ModelParameterSet.objects.get(
            model_type="damages_expected", canonical_key='{"GWL":2}'
        )
        additional = DamagesExpected.objects.create(
            parameter_set=generated_parameters,
            feature=self.other_feature,
            hazard="fluvial",
            protection_standard=0,
            ead_mean=888,
        )
        self.seed("--clear")
        self.assertEqual(
            set(DamagesExpected.objects.values_list("id", flat=True)),
            {imported.id, additional.id},
        )
        self.assertTrue(
            ModelParameterSet.objects.filter(pk=existing_parameters.pk).exists()
        )
        self.assertTrue(
            ModelParameterSet.objects.filter(pk=generated_parameters.pk).exists()
        )
        self.assertEqual(AdaptationCostBenefit.objects.count(), 0)

    def test_rolls_back_partial_batches_and_ownership_record_on_failure(self):
        insert = Command.insert
        calls = 0

        def failing_insert(command, *args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected failure")
            insert(command, *args)

        with patch.object(Command, "insert", autospec=True, side_effect=failing_insert):
            with self.assertRaisesMessage(RuntimeError, "injected failure"):
                self.seed()
        for model in (
            *RESULT_MODELS.values(),
            ModelParameterSet,
            ModelParameter,
            SyntheticDataRun,
        ):
            self.assertEqual(model.objects.count(), 0)

    def test_supports_layer_sampling_explicit_protectors_and_hazard_filter(self):
        self.seed(
            "--limit-per-layer",
            "3",
            "--hazard",
            "fluvial",
            "--protector-id",
            str(self.other_feature.id),
        )
        ids = set(DamagesExpected.objects.values_list("feature_id", flat=True))
        self.assertEqual(len(ids), 3)
        self.assertEqual(
            set(
                AdaptationCostBenefit.objects.values_list(
                    "protector_feature_id", flat=True
                )
            ),
            {self.other_feature.id},
        )
        self.assertEqual(
            set(DamagesExpected.objects.values_list("hazard", flat=True)), {"fluvial"}
        )
        self.seed("--clear")
        self.seed(
            "--limit-per-layer",
            "3",
            "--hazard",
            "fluvial",
            "--protector-id",
            str(self.other_feature.id),
        )
        self.assertEqual(
            ids, set(DamagesExpected.objects.values_list("feature_id", flat=True))
        )

    def test_validates_selection_and_restricts_writes_to_development(self):
        for args in (
            ("--layer", "missing"),
            ("--hazard", "missing"),
            ("--protector-id", "-1"),
            ("--limit-per-layer", "0"),
            ("--name", "../invalid"),
        ):
            with self.subTest(args=args), self.assertRaises(CommandError):
                self.seed(*args)
        self.source_options.return_value = None
        self.source_options.side_effect = lambda *args, **kwargs: [
            {"GWL": "2", "RP": "0"}
        ]
        with self.assertRaisesMessage(CommandError, "positive integer return periods"):
            self.seed()
        with override_settings(DEBUG=False), self.assertRaisesMessage(
            CommandError, "DEBUG=True"
        ):
            self.seed()
        self.assertFalse(SyntheticDataRun.objects.exists())

    def test_full_coverage_tracks_only_inserted_ids_and_preserves_existing_results(
        self,
    ):
        parameters = ModelParameterSet.for_values("damages_expected", {"GWL": 0.75})
        imported = DamagesExpected.objects.create(
            parameter_set=parameters,
            feature=self.features[0],
            hazard="fluvial",
            protection_standard=0,
            ead_mean=777,
        )
        with patch(
            "map.management.commands.seed_synthetic_results.FULL_BATCH_SIZE", 5
        ), patch(
            "map.management.commands.seed_synthetic_results.FULL_PROTECTOR_GROUP_SIZE",
            5,
        ):
            self.seed("--all-features")
        run = SyntheticDataRun.objects.get()
        expected = {
            "damages_expected": 95,
            "damages_rp": 72,
            "damages_npv": 48,
            "adaptation": 144,
        }
        for key, manifest in run.result_ids.items():
            self.assertEqual(manifest["count"], expected[key])
            owned_ids = {
                value
                for first, last in manifest["ranges"]
                for value in range(first, last + 1)
            }
            self.assertEqual(len(owned_ids), expected[key])
            self.assertTrue(
                RESULT_MODELS[key].objects.filter(id__in=owned_ids).count()
                == len(owned_ids)
            )
            if key == "damages_expected":
                self.assertNotIn(imported.id, owned_ids)
        self.assertEqual(
            DamagesExpected.objects.values("feature_id").distinct().count(), 12
        )
        self.assertTrue(DamagesExpected.objects.filter(ead_mean__isnull=True).exists())
        self.assertTrue(DamagesExpected.objects.filter(ead_mean=0).exists())
        self.assertEqual(
            set(
                AdaptationCostBenefit.objects.values_list(
                    "protector_feature_id", flat=True
                )
            ),
            {self.features[index].id for index in (0, 5, 10)},
        )
        for row in DamagesExpected.objects.exclude(ead_mean__isnull=True).exclude(
            id=imported.id
        ):
            self.assertLessEqual(row.ead_amin, row.ead_mean)
            self.assertLessEqual(row.ead_mean, row.ead_amax)
        imported.refresh_from_db()
        self.assertEqual(imported.ead_mean, 777)
        self.seed("--clear")
        self.assertEqual(
            list(DamagesExpected.objects.values_list("id", flat=True)), [imported.id]
        )
        for key in ("damages_rp", "damages_npv", "adaptation"):
            self.assertFalse(RESULT_MODELS[key].objects.exists())

    def imported_results(self):
        dimensions = {
            "damages_expected": {"protection_standard": 0, "ead_mean": 777},
            "damages_rp": {"rp": 100, "damage_mean": 777},
            "damages_npv": {"ead_mean": 777},
            "adaptation": {
                "adaptation_name": "Imported option",
                "adaptation_protection_level": 100,
                "adaptation_cost": 777,
            },
        }
        for key, model in RESULT_MODELS.items():
            model.objects.create(
                parameter_set=ModelParameterSet.for_values(
                    key, {"rcp": "baseline", "epoch": 2010}
                ),
                feature=self.other_feature,
                hazard="cyclone",
                **dimensions[key],
            )

    def test_replace_preview_then_replaces_all_results_and_preserves_features(self):
        self.imported_results()
        original = self.snapshot()
        features = list(Feature.objects.order_by("id").values())
        output = self.seed("--replace", "--all-features", "--dry-run")
        self.assertIn("remove ALL existing result rows", output)
        self.assertEqual(original, self.snapshot())
        self.seed("--replace", "--all-features")
        self.assertEqual(features, list(Feature.objects.order_by("id").values()))
        for model in RESULT_MODELS.values():
            self.assertFalse(model.objects.filter(hazard="cyclone").exists())
            self.assertFalse(model.objects.filter(feature=self.other_feature).exists())
        self.assertEqual(DamagesExpected.objects.count(), 96)
        self.assertTrue(SyntheticDataRun.objects.get().config["replace"])

    def test_replace_failure_restores_old_results_and_run_ownership(self):
        self.seed("--name", "previous")
        self.imported_results()
        original = self.snapshot()
        original_runs = list(SyntheticDataRun.objects.values())
        from map.synthetic_sql import insert_fixtures

        calls = 0

        def failing_insert(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected bulk failure")
            return insert_fixtures(*args)

        with patch(
            "map.management.commands.seed_synthetic_results.insert_fixtures",
            side_effect=failing_insert,
        ):
            with self.assertRaisesMessage(RuntimeError, "injected bulk failure"):
                self.seed("--replace", "--all-features")
        self.assertEqual(original, self.snapshot())
        self.assertEqual(original_runs, list(SyntheticDataRun.objects.values()))

    def test_full_replacement_checks_foreign_keys_during_each_insert(self):
        from map.synthetic_sql import insert_fixtures

        def checked_insert(*args):
            caught = False
            with transaction.atomic():
                try:
                    DamagesExpected.objects.create(
                        parameter_set=ModelParameterSet.objects.filter(
                            model_type="damages_expected"
                        ).first(),
                        feature_id=2147483647,
                        hazard="fluvial",
                        protection_standard=0,
                    )
                except IntegrityError:
                    caught = True
                finally:
                    transaction.set_rollback(True)
            self.assertTrue(
                caught, "Full loads must not defer FK trigger events until commit."
            )
            return insert_fixtures(*args)

        with patch(
            "map.management.commands.seed_synthetic_results.insert_fixtures",
            side_effect=checked_insert,
        ):
            self.seed("--replace", "--all-features")

    def test_seeded_results_work_with_discovery_lookup_sorting_and_protected_features(
        self,
    ):
        self.seed()
        client = APIClient()
        client.force_authenticate(
            User.objects.create_user(username="synthetic-tests", is_superuser=True)
        )
        rows = client.get(
            "/map/model-scenarios/damages_expected",
            {"layer": "roads", "hazard": "fluvial"},
        ).json()
        self.assertEqual(len(rows), 4)
        query = {
            "layer": "roads",
            "field": "ead_mean",
            "dimensions": '{"hazard":"fluvial","parameters":{"GWL":0.75},"protection_standard":0}',
        }

        response = client.post(
            "/map/attributes/damages_expected?" + urlencode(query),
            {"ids": [self.features[0].id]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()[str(self.features[0].id)], 0)
        response = client.get("/map/features/sorted-by/damages_expected", query)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 12)
        protector = self.features[0].id
        response = client.get(
            "/map/features/" + str(protector) + "/protected-by",
            {"parameters": '{"GWL":0.75}'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 36)
        response = client.get(
            "/map/model-scenarios/adaptation", {"protector_id": protector}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 12)
