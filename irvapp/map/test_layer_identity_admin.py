from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from map.models import Dataset, FeatureLayer, LayerIdentity, RasterLayer
from raster.models import RasterTileSource


class LayerIdentityAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser(username="admin", password="test"))
        FeatureLayer.objects.create(layer_name="roads", sector="", subsector="", asset_type="")
        dataset = Dataset.objects.create(id="hazards", label="Hazards", group="hazards")
        source = RasterTileSource.objects.create(keys=["type"])
        RasterLayer.objects.create(id="rain", dataset=dataset, tile_source=source,
            label="Rain", quantity="depth", unit="m", stacking_order=0, display_order=0)
        LayerIdentity.objects.create(id="unattached", kind="feature")

    def test_view_only_staff_can_open_attached_identities(self):
        viewer = User.objects.create_user(username="viewer", is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(
            content_type__app_label="map", codename="view_layeridentity",
        ))
        self.client.force_login(viewer)

        for identity_id in ("roads", "rain"):
            with self.subTest(identity_id=identity_id):
                url = reverse("admin:map_layeridentity_change", args=[identity_id])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context["has_change_permission"])
                self.assertNotIn("kind", response.context["adminform"].form.fields)

    def test_attached_kind_is_disabled_and_rejects_tampered_posts(self):
        for identity_id, original, attempted in (("roads", "feature", "raster"), ("rain", "raster", "feature")):
            with self.subTest(identity_id=identity_id):
                url = reverse("admin:map_layeridentity_change", args=[identity_id])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["adminform"].form.fields["kind"].disabled)
                response = self.client.post(url, {"id": identity_id, "kind": attempted, "_save": "Save"})
                self.assertEqual(response.status_code, 200)
                self.assertFormError(response.context["adminform"].form, "kind", "Cannot change the type while a layer is attached.")
                self.assertEqual(LayerIdentity.objects.get(pk=identity_id).kind, original)

    def test_attached_identity_saves_without_kind_in_post(self):
        url = reverse("admin:map_layeridentity_change", args=["roads"])
        response = self.client.post(url, {"id": "roads", "_save": "Save"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(LayerIdentity.objects.get(pk="roads").kind, "feature")

    def test_unattached_identity_can_change_kind(self):
        url = reverse("admin:map_layeridentity_change", args=["unattached"])
        response = self.client.get(url)
        self.assertFalse(response.context["adminform"].form.fields["kind"].disabled)
        response = self.client.post(url, {"id": "unattached", "kind": "raster", "_save": "Save"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(LayerIdentity.objects.get(pk="unattached").kind, "raster")

    def test_model_validation_rejects_attached_kind_change(self):
        identity = LayerIdentity.objects.get(pk="roads")
        identity.kind = "raster"
        with self.assertRaises(ValidationError) as error:
            identity.full_clean()
        self.assertIn("kind", error.exception.message_dict)
