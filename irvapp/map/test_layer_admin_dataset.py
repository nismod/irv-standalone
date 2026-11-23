from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from map.models import Dataset, FeatureLayer, LayerIdentity, RasterLayer
from raster.models import RasterTileSource


class LayerAdminDatasetTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username="admin", password="test")
        self.client.force_login(self.admin_user)
        self.original = Dataset.objects.create(id="original", label="Original", group="hazards")
        self.other = Dataset.objects.create(id="other", label="Other", group="hazards")
        self.source = RasterTileSource.objects.create(keys=["type"])
        LayerIdentity.objects.create(id="roads", kind="feature", dataset=self.original)
        FeatureLayer.objects.create(layer_name="roads", sector="transport", subsector="road", asset_type="edge")
        LayerIdentity.objects.create(id="rain", kind="raster", dataset=self.original)
        RasterLayer.objects.create(id="rain", tile_source=self.source, label="Rain", quantity="depth",
                                   unit="m", stacking_order=0, display_order=0)

    def payload(self, kind, layer_id, dataset_id):
        common = {"identity": layer_id, "dataset": dataset_id, "stacking_order": "0", "display_order": "0", "_save": "Save"}
        if kind == "featurelayer":
            return {**common, "sector": "transport", "subsector": "road", "asset_type": "edge"}
        return {**common, "tile_source": self.source.pk, "label": "Rain", "quantity": "depth", "unit": "m"}

    def test_change_and_clear_dataset_from_each_layer_page(self):
        for kind, layer_id in (("featurelayer", "roads"), ("rasterlayer", "rain")):
            with self.subTest(kind=kind):
                url = reverse(f"admin:map_{kind}_change", args=[layer_id])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["adminform"].form["dataset"].value(), self.original.pk)
                response = self.client.post(url, self.payload(kind, layer_id, self.other.pk))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(LayerIdentity.objects.get(pk=layer_id).dataset_id, self.other.pk)
                response = self.client.post(url, self.payload(kind, layer_id, ""))
                self.assertEqual(response.status_code, 302)
                self.assertIsNone(LayerIdentity.objects.get(pk=layer_id).dataset_id)
                api = APIClient()
                api.force_authenticate(self.admin_user)
                endpoint = "feature-layers" if kind == "featurelayer" else "raster-layers"
                self.assertEqual(api.get(f"/map/{endpoint}/{layer_id}").status_code, 403)

    def test_invalid_dataset_does_not_save_layer_or_identity(self):
        url = reverse("admin:map_featurelayer_change", args=["roads"])
        payload = self.payload("featurelayer", "roads", "not-a-dataset")
        payload["sector"] = "changed"
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("dataset", response.context["adminform"].form.errors)
        self.assertEqual(LayerIdentity.objects.get(pk="roads").dataset_id, self.original.pk)
        self.assertEqual(FeatureLayer.objects.get(pk="roads").sector, "transport")

    def test_add_layer_can_assign_or_preserve_identity_dataset(self):
        LayerIdentity.objects.create(id="new-roads", kind="feature", dataset=self.original)
        LayerIdentity.objects.create(id="new-rain", kind="raster")
        feature_url = reverse("admin:map_featurelayer_add")
        self.assertEqual(self.client.post(feature_url, self.payload("featurelayer", "new-roads", "")).status_code, 302)
        self.assertEqual(LayerIdentity.objects.get(pk="new-roads").dataset_id, self.original.pk)
        raster_url = reverse("admin:map_rasterlayer_add")
        self.assertEqual(self.client.post(raster_url, self.payload("rasterlayer", "new-rain", self.other.pk)).status_code, 302)
        self.assertEqual(LayerIdentity.objects.get(pk="new-rain").dataset_id, self.other.pk)

    def test_staff_without_identity_change_permission_cannot_reassign_dataset(self):
        staff = User.objects.create_user(username="layer-editor", is_staff=True)
        permissions = Permission.objects.filter(content_type__app_label="map", codename__in=[
            "view_featurelayer", "add_featurelayer", "change_featurelayer", "view_layeridentity", "view_dataset",
        ])
        staff.user_permissions.add(*permissions)
        self.client.force_login(staff)
        url = reverse("admin:map_featurelayer_change", args=["roads"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("dataset", response.context["adminform"].form.fields)
        response = self.client.post(url, self.payload("featurelayer", "roads", self.other.pk))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(LayerIdentity.objects.get(pk="roads").dataset_id, self.original.pk)
        response = self.client.get(reverse("admin:map_featurelayer_add"))
        self.assertEqual(response.status_code, 200)
