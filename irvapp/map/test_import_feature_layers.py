from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from map.models import Dataset, FeatureLayer, LayerIdentity


class ImportFeatureLayersTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "layers.csv"

    def import_rows(self, rows):
        self.path.write_text("layer,sector,subsector,asset_type\n" + rows)
        output = StringIO()
        call_command("import_feature_layers", str(self.path), stdout=output)
        return output.getvalue()

    def test_rerun_preserves_curated_metadata_and_reports_unassigned(self):
        dataset = Dataset.objects.create(id="data", label="Data", group="group")
        layer = FeatureLayer.objects.create(
            layer_name="roads", sector="curated", subsector="road", asset_type="edge",
            display_order=7, stacking_order=9,
        )
        LayerIdentity.objects.filter(pk="roads").update(dataset=dataset)
        rows = "roads,transport,road,edge\nrail,transport,rail,track\n"
        output = self.import_rows(rows)
        self.assertIn("Existing metadata differs", output)
        self.assertIn("rail", output)
        self.assertEqual(LayerIdentity.objects.get(pk="rail").kind, "feature")
        layer.refresh_from_db()
        self.assertEqual((layer.sector, layer.display_order, layer.stacking_order), ("curated", 7, 9))
        self.assertEqual(layer.identity.dataset, dataset)
        self.assertIn("Created 0", self.import_rows(rows))
        self.assertEqual(FeatureLayer.objects.count(), 2)

    def test_collision_rolls_back_all_layers(self):
        LayerIdentity.objects.create(id="raster", kind="raster")
        with self.assertRaisesMessage(CommandError, "belongs to raster"):
            self.import_rows("new,transport,road,edge\nraster,transport,road,edge\n")
        self.assertFalse(LayerIdentity.objects.filter(pk="new").exists())

    def test_conflicting_input_definitions_are_rejected(self):
        with self.assertRaisesMessage(CommandError, "conflicting definitions"):
            self.import_rows("roads,transport,road,edge\nroads,transport,road,node\n")
        self.assertFalse(FeatureLayer.objects.exists())
