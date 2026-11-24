from importlib import import_module
from types import SimpleNamespace

from django.contrib.gis.geos import Point
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from map.models import DamagesExpected, ModelParameterSet


def make_parameter_set(model_type, **values):
    return ModelParameterSet.for_values(model_type, values)


class NpvRemovalMigrationTests(TransactionTestCase):
    def test_reverse_recreates_sequence_and_forward_removes_it(self):
        before = [("map", "0034_feature_layer_style_permissions")]
        after = [("map", "0035_delete_damagesnpv")]
        self.addCleanup(
            lambda: MigrationExecutor(connection).migrate(
                MigrationExecutor(connection).loader.graph.leaf_nodes()
            )
        )
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        identity = apps.get_model("map", "LayerIdentity").objects.create(
            id="npv-migration-test", kind="feature"
        )
        layer = apps.get_model("map", "FeatureLayer").objects.create(
            identity=identity, sector="transport", subsector="road", asset_type="edge"
        )
        feature = apps.get_model("map", "Feature").objects.create(
            string_id="road", layer=layer, properties={}, geom=Point(0, 0, srid=4326)
        )
        parameters = apps.get_model("map", "ModelParameterSet").objects.create(
            model_type="damages_npv", canonical_key="{}"
        )
        damage = apps.get_model("map", "DamagesNpv").objects.create(
            feature=feature, parameter_set=parameters, hazard="flood"
        )
        self.assertIsNotNone(damage.id)
        MigrationExecutor(connection).migrate(after)
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('damages_npv_id_seq')")
            self.assertIsNone(cursor.fetchone()[0])
        # A second rollback verifies that reapplying removed the owned sequence.
        MigrationExecutor(connection).migrate(before)


class ParameterKeyMigrationTests(TransactionTestCase):
    def setUp(self):
        from map.models import Feature, FeatureLayer

        self.addCleanup(
            lambda: MigrationExecutor(connection).migrate(
                MigrationExecutor(connection).loader.graph.leaf_nodes()
            )
        )
        executor = MigrationExecutor(connection)
        target = [("map", "0034_feature_layer_style_permissions")]
        executor.migrate(target)
        self.migration_apps = executor.loader.project_state(target).apps
        layer = FeatureLayer.objects.create(
            layer_name="roads", sector="transport", subsector="road", asset_type="edge"
        )
        self.feature_1 = Feature.objects.create(
            string_id="road-1", layer=layer, properties={}, geom=Point(0, 0, srid=4326)
        )

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
        migration.normalize_parameter_keys(self.migration_apps, SimpleNamespace(connection=connection))
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
        migration.normalize_parameter_keys(self.migration_apps, SimpleNamespace(connection=connection))
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
            migration.normalize_parameter_keys(self.migration_apps, SimpleNamespace(connection=connection))
        self.assertEqual(ModelParameterSet.objects.count(), 2)
        self.assertEqual(
            list(DamagesExpected.objects.order_by("ead_mean").values_list("ead_mean", flat=True)),
            [10, 20],
        )

