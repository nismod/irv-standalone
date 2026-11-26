"""Integration checks for the Jamaica ETL (requires ETL dependencies)."""
import importlib.util
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import skipUnless

from django.contrib.gis.geos import Point
from django.test import TestCase

from map.models import AdaptationCostBenefit, DamagesExpected, DamagesRp, Feature, FeatureLayer

ETL_SCRIPTS = Path(__file__).resolve().parents[2] / 'etl' / 'scripts'
sys.path.insert(0, str(ETL_SCRIPTS))
HAS_ETL = all(importlib.util.find_spec(name) is not None for name in ('pyarrow', 'fiona', 'shapely'))


@skipUnless(HAS_ETL, 'requires pyarrow from the ETL environment')
class JamaicaETLTests(TestCase):
    def setUp(self):
        layer = FeatureLayer.objects.create(layer_name='roads', sector='transport', subsector='road', asset_type='edge')
        self.feature = Feature.objects.create(id=10, string_id='r1', layer=layer, properties={'asset_id': 'r1', 'asset_type': 'edge'}, geom=Point(1, 2, srid=4326))
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def parquet(self, name, data):
        import pyarrow as pa
        import pyarrow.parquet as pq
        path = Path(self.tmp.name) / name
        with path.open("wb") as output:
            pq.write_table(pa.table(data), output)
        return path

    def test_expected_import_rerun_and_atomic_duplicate(self):
        from damages_exp_to_db import yield_expected_damages
        from result_import import import_results
        fields = ['ead_amin', 'ead_mean', 'ead_amax', 'eael_amin', 'eael_mean', 'eael_amax']
        keys = ['parameter_set', 'feature', 'hazard', 'protection_standard']
        path = self.parquet('expected.parquet', {'uid': [10], 'hazard': ['fluvial'], 'rcp': ['4.5'], 'epoch': [2050], 'EAD_undefended_mean': [7.0]})
        import_results(DamagesExpected, 'damages_expected', keys, fields, yield_expected_damages(path))
        import_results(DamagesExpected, 'damages_expected', keys, fields, yield_expected_damages(path))
        row = DamagesExpected.objects.get()
        self.assertEqual(row.parameter_set.values, {'rcp': '4.5', 'epoch': 2050})
        self.assertEqual(row.ead_mean, 7)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            import_results(DamagesExpected, 'damages_expected', keys, fields,
                           list(yield_expected_damages(path)) * 2)
        self.assertEqual(DamagesExpected.objects.count(), 1)

    def test_duplicate_after_first_batch_rolls_back_results_and_parameters(self):
        from map.models import ModelParameterSet
        from result_import import import_results

        keys = ['parameter_set', 'feature', 'hazard', 'rp']
        fields = ['exposure', 'damage_amin', 'damage_mean', 'damage_amax',
                  'loss_amin', 'loss_mean', 'loss_amax']
        params = {'rcp': '8.5', 'epoch': 2080}

        def rows():
            for rp in range(1001):
                yield params, {'feature_id': 10, 'hazard': 'fluvial', 'rp': rp, 'exposure': 1}
            yield params, {'feature_id': 10, 'hazard': 'fluvial', 'rp': 0, 'exposure': 2}

        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            import_results(DamagesRp, 'damages_rp', keys, fields, rows())
        self.assertFalse(DamagesRp.objects.exists())
        self.assertFalse(ModelParameterSet.objects.filter(model_type='damages_rp').exists())

    def test_return_period_outer_join_and_uid_validation(self):
        from damages_rp_to_db import yield_return_period_damages
        from result_import import import_results
        column = 'fluvial__rp_100__rcp_4.5__epoch_2050__conf_None'
        exposure = self.parquet('exposure.parquet', {'uid': [10], column: [5.]})
        damage = self.parquet('damage.parquet', {'uid': [10], column + '_mean': [0.]})
        loss = self.parquet('loss.parquet', {'uid': [10], column + '_mean': [3.]})
        keys = ['parameter_set', 'feature', 'hazard', 'rp']
        fields = ['exposure', 'damage_amin', 'damage_mean', 'damage_amax', 'loss_amin', 'loss_mean', 'loss_amax']
        import_results(DamagesRp, 'damages_rp', keys, fields, yield_return_period_damages(exposure, damage, loss))
        row = DamagesRp.objects.get()
        self.assertEqual((row.exposure, row.damage_mean, row.loss_mean), (5, 0, 3))
        other = self.parquet('other.parquet', {'uid': [99], column: [2.]})
        with self.assertRaisesRegex(ValueError, 'different UID order'):
            list(yield_return_period_damages(other, damage, loss))

    def test_adaptation_upsert_rejects_changed_protector(self):
        from adaptation_to_db import parse_adaptation, yield_adaptation
        from result_import import import_results
        import pandas as pd
        Feature.objects.create(id=11, string_id='p1', layer=self.feature.layer,
                               properties={}, geom=Point(2, 3, srid=4326))
        data = pd.DataFrame([{'uid': 10, 'adaptation_option': 'raise',
                              'flood_depth_protection_level': 1.0, 'adapt_cost_npv': 3.0,
                              'fluvial__rcp_4.5__avoided_EAD_mean': 9.0}])
        rows = list(yield_adaptation(parse_adaptation(data)))
        keys = ['parameter_set', 'feature', 'hazard', 'adaptation_name', 'adaptation_protection_level']
        fields = ['protector_feature_id', 'adaptation_cost', 'avoided_ead_amin', 'avoided_ead_mean', 'avoided_ead_amax', 'avoided_eael_amin', 'avoided_eael_mean', 'avoided_eael_amax']
        import_results(AdaptationCostBenefit, 'adaptation', keys, fields, rows)
        self.assertEqual(AdaptationCostBenefit.objects.get().protector_feature_id, 10)
        params, values = rows[0]
        values = {**values, 'protector_feature_id': 11}
        with self.assertRaisesRegex(ValueError, 'Conflicting protector'):
            import_results(AdaptationCostBenefit, 'adaptation', keys, fields, [(params, values)])
        self.assertEqual(AdaptationCostBenefit.objects.get().protector_feature_id, 10)

    def test_coastal_adaptation_preserves_mapped_protector(self):
        from coastal_adaptation_to_db import match_asset_to_protector, parse_adaptation, yield_adaptation
        from result_import import import_results
        import pandas as pd
        Feature.objects.create(id=11, string_id='p1', layer=self.feature.layer,
                               properties={}, geom=Point(2, 3, srid=4326))
        mappings = pd.DataFrame({'flood_id': ['p1']}, index=['r1'])
        protectors = pd.DataFrame({'uid': [11]}, index=['p1'])
        self.assertEqual(list(match_asset_to_protector(['r1'], protectors, mappings)), [11])
        data = pd.DataFrame([{'uid': 10, 'protector_feature_id': 11,
                              'adaptation_option': 'protect', 'adapt_cost_npv': 3.0,
                              'coastal__rcp_4.5__avoided_EAD_mean': 9.0}])
        keys = ['parameter_set', 'feature', 'hazard', 'adaptation_name', 'adaptation_protection_level']
        fields = ['protector_feature_id', 'adaptation_cost', 'avoided_ead_amin', 'avoided_ead_mean', 'avoided_ead_amax', 'avoided_eael_amin', 'avoided_eael_mean', 'avoided_eael_amax']
        import_results(AdaptationCostBenefit, 'adaptation', keys, fields, yield_adaptation(parse_adaptation(data)))
        result = AdaptationCostBenefit.objects.get()
        self.assertEqual((result.protector_feature_id, result.hazard, result.adaptation_protection_level), (11, 'flooding', 100))

    def test_feature_reload_preserves_results_and_rolls_back_unsafe_removal(self):
        from networks_to_db import reload_features
        from map.models import ModelParameterSet
        params = ModelParameterSet.for_values('damages_expected', {'rcp': '4.5', 'epoch': 2050})
        DamagesExpected.objects.create(feature=self.feature, hazard='fluvial', parameter_set=params,
                                       protection_standard=0, ead_mean=5)
        replacement = Feature(id=10, string_id='updated', layer_id='roads', properties={}, geom=Point(3, 4, srid=4326))
        reload_features([replacement], ['roads'])
        self.assertEqual(DamagesExpected.objects.get().ead_mean, 5)
        other = Feature(id=12, string_id='new', layer_id='roads', properties={}, geom=Point(1, 2, srid=4326))
        with self.assertRaisesRegex(ValueError, 'referenced by results'):
            reload_features([other], ['roads'])
        self.assertFalse(Feature.objects.filter(pk=12).exists())
        self.assertEqual(Feature.objects.get(pk=10).string_id, 'updated')

    def test_export_has_database_uid_and_no_embedded_scenarios(self):
        from db_to_geojsonseq import feature_as_geojson
        result = feature_as_geojson(self.feature)
        self.assertEqual(result['id'], 10)
        self.assertEqual(result['properties']['uid'], 10)
        self.assertEqual(result['geometry']['type'], 'Point')
