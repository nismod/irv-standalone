import io
from types import SimpleNamespace
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

    @patch("raster.views.tiles._get_singleband_image")
    @patch("raster.views.tiles.RasterTileSource.objects.values_list")
    def test_renders_tile_with_explicit_internal_colormap(
        self,
        mock_values_list,
        mock_get_singleband_image,
    ):
        self.client.force_authenticate(user=self.user)
        mock_values_list.return_value.get.return_value = (
            "terracotta_land_cover"
        )
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
        mock_values_list.assert_called_once_with("database", flat=True)
        mock_values_list.return_value.get.assert_called_once_with(
            domain="land_cover"
        )

    @patch("raster.views.tiles.RasterTileSource.objects.values_list")
    def test_requires_explicit_color_map_when_not_builtin(
        self,
        mock_values_list,
    ):
        self.client.force_authenticate(user=self.user)
        mock_values_list.return_value.get.return_value = "terracotta_aqueduct"

        response = self.client.get(
            "/tiles/raster/aqueduct/a/b/3/1/2.png?colormap=explicit"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "colormap=explicit requires explicit_color_map to be included",
        )
        mock_values_list.assert_called_once_with("database", flat=True)
        mock_values_list.return_value.get.assert_called_once_with(
            domain="aqueduct"
        )


class RasterTileSourceViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="source-user",
            password="testpass",
        )

    def test_sources_requires_authentication(self):
        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 403)

    @patch("raster.views.sources.RasterTileSource.objects.all")
    def test_lists_tile_sources(self, mock_all):
        self.client.force_authenticate(user=self.user)
        mock_all.return_value = [
            SimpleNamespace(
                id=1,
                domain="land_cover",
                name="Land Cover",
                group="Exposure",
                description="Land cover tiles",
                license="CC-BY",
                keys=["region", "year"],
            )
        ]

        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["domain"], "land_cover")

    @patch("raster.views.sources.RasterTileSource.objects.get")
    def test_returns_single_tile_source(self, mock_get):
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = SimpleNamespace(
            id=1,
            domain="land_cover",
            name="Land Cover",
            group="Exposure",
            description="Land cover tiles",
            license="CC-BY",
            keys=["region", "year"],
        )

        response = self.client.get("/tiles/raster/sources/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 1)

    @patch("raster.views.sources._source_options")
    @patch("raster.views.sources.RasterTileSource.objects.get")
    def test_returns_source_domains(
        self,
        mock_get,
        mock_source_options,
    ):
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = SimpleNamespace(
            domain="land_cover",
            database="terracotta_land_cover",
            keys=["region", "year"],
        )
        mock_source_options.return_value = [
            {"region": "global", "year": "2020"}
        ]

        response = self.client.get(
            "/tiles/raster/sources/land_cover/domains"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["domains"],
            [{"region": "global", "year": "2020"}],
        )
        mock_get.assert_called_once_with(domain="land_cover")
        mock_source_options.assert_called_once_with(
            "terracotta_land_cover", filters=None
        )

    @patch("raster.views.sources._source_options")
    @patch("raster.views.sources.RasterTileSource.objects.get")
    def test_filters_source_domains_by_terracotta_type(
        self,
        mock_get,
        mock_source_options,
    ):
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = SimpleNamespace(
            domain="coastal",
            database="terracotta.sqlite",
            keys=["type", "rp", "rcp", "epoch", "confidence"],
        )
        mock_source_options.return_value = []

        response = self.client.get(
            "/tiles/raster/sources/coastal/domains"
        )

        self.assertEqual(response.status_code, 200)
        mock_source_options.assert_called_once_with(
            "terracotta.sqlite", filters={"type": "coastal"}
        )
