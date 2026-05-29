import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .internal.colormaps import CATEGORICAL_COLOR_MAPS
from .views import _parse_keys


class ParseKeysTests(TestCase):
    def test_raises_for_empty_keys(self):
        with self.assertRaises(ValueError):
            _parse_keys("")

    def test_raises_for_slash_only_keys(self):
        with self.assertRaises(ValueError):
            _parse_keys("///")


class RasterTileImageViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tile-user",
            password="testpass",
        )

    def test_requires_authentication(self):
        response = self.client.get(
            "/tiles/raster/land_cover/a/b/3/1/2.png"
        )

        self.assertEqual(response.status_code, 403)

    @patch("raster.views._get_singleband_image")
    @patch("raster.views._tile_db_from_domain")
    def test_renders_tile_with_explicit_internal_colormap(
        self,
        mock_tile_db_from_domain,
        mock_get_singleband_image,
    ):
        self.client.force_authenticate(user=self.user)
        mock_tile_db_from_domain.return_value = "terracotta_land_cover"
        mock_get_singleband_image.return_value = io.BytesIO(b"png-bytes")

        response = self.client.get(
            (
                "/tiles/raster/land_cover/a/b/3/1/2.png"
                "?colormap=explicit"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"png-bytes")
        mock_get_singleband_image.assert_called_once_with(
            "terracotta_land_cover",
            ["a", "b"],
            [1, 2, 3],
            {"colormap": CATEGORICAL_COLOR_MAPS["land_cover"]},
        )

    @patch("raster.views._tile_db_from_domain")
    def test_requires_explicit_color_map_when_not_builtin(
        self,
        mock_tile_db_from_domain,
    ):
        self.client.force_authenticate(user=self.user)
        mock_tile_db_from_domain.return_value = "terracotta_aqueduct"

        response = self.client.get(
            "/tiles/raster/aqueduct/a/b/3/1/2.png?colormap=explicit"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "colormap=explicit requires explicit_color_map to be included",
        )
