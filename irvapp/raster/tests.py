import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from api.models import Dataset
from raster import ingestion as ingest

from .internal.colormaps import CATEGORICAL_COLOR_MAPS
from .models import RasterTileSource
from .views import _parse_keys


class DiscoverRastersTests(SimpleTestCase):
    def test_discovers_keys_from_custom_template(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            raster = base_path / "flood" / "2050_rcp_4x5.tif"
            raster.parent.mkdir()
            raster.touch()

            keys, rasters = ingest.discover_rasters(
                str(base_path / "{hazard}" / "{epoch}_rcp_{scenario}.tif")
            )

            self.assertEqual(keys, ["hazard", "epoch", "scenario"])
            self.assertEqual(rasters, {("flood", "2050", "4x5"): str(raster)})

    def test_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            (base_path / "one").mkdir()
            (base_path / "two").mkdir()
            (base_path / "one" / "flood.tif").touch()
            (base_path / "two" / "flood.tif").touch()

            with self.assertRaisesRegex(ValueError, "duplicate key values"):
                ingest.discover_rasters(str(base_path / "{}" / "{hazard}.tif"))

    def test_repeated_placeholder_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            (base_path / "flood").mkdir()
            matching = base_path / "flood" / "flood.tif"
            matching.touch()
            (base_path / "flood" / "wind.tif").touch()

            _, rasters = ingest.discover_rasters(
                str(base_path / "{hazard}" / "{hazard}.tif")
            )

            self.assertEqual(rasters, {("flood",): str(matching)})


class InferDatabaseProviderTests(SimpleTestCase):
    def test_infers_postgresql_from_common_url_variants(self):
        self.assertEqual(
            ingest.infer_database_provider("postgres://user:pass@host/db"),
            "postgresql",
        )
        self.assertEqual(
            ingest.infer_database_provider(
                "postgresql+psycopg://user:pass@host/db"
            ),
            "postgresql",
        )

    def test_falls_back_to_sqlite_for_unknown_schemes(self):
        self.assertEqual(
            ingest.infer_database_provider("oracle://user:pass@host/db"),
            "sqlite",
        )


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
        self.access_group = Group.objects.create(name="tile-access")
        self.user.groups.add(self.access_group)
        land_cover_dataset = Dataset.objects.create(
            id="land_cover",
            label="Land Cover",
            group="exposure",
            unit="class",
            stacking_order=1,
            display_order=1,
        )
        land_cover_dataset.access_groups.add(self.access_group)
        aqueduct_dataset = Dataset.objects.create(
            id="aqueduct",
            label="Aqueduct",
            group="hazards",
            unit="m",
            stacking_order=2,
            display_order=2,
        )
        aqueduct_dataset.access_groups.add(self.access_group)
        RasterTileSource.objects.create(
            domain="land_cover",
            name="Land Cover",
            group="Exposure",
            keys=["region", "year"],
            database="terracotta_land_cover",
            dataset=land_cover_dataset,
        )
        RasterTileSource.objects.create(
            domain="aqueduct",
            name="Aqueduct",
            group="Hazards",
            keys=["region", "year"],
            database="terracotta_aqueduct",
            dataset=aqueduct_dataset,
        )

    def test_requires_authentication(self):
        response = self.client.get(
            "/tiles/raster/land_cover/a/b/3/1/2.png"
        )

        self.assertEqual(response.status_code, 403)

    @patch("raster.views.tiles._get_singleband_image")
    def test_renders_tile_with_explicit_internal_colormap(
        self,
        mock_get_singleband_image,
    ):
        self.client.force_authenticate(user=self.user)
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

    def test_requires_explicit_color_map_when_not_builtin(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/tiles/raster/aqueduct/a/b/3/1/2.png?colormap=explicit"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "colormap=explicit requires explicit_color_map to be included",
        )

    @patch("raster.views.tiles._get_singleband_image")
    def test_restricted_tile_is_not_rendered_for_non_member(
        self,
        mock_get_singleband_image,
    ):
        source = RasterTileSource.objects.get(domain="land_cover")
        dataset = source.dataset
        dataset.access_groups.clear()
        dataset.access_groups.add(Group.objects.create(name="restricted"))
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/tiles/raster/land_cover/a/b/3/1/2.png"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "You do not have permission to access this raster source.",
        )
        mock_get_singleband_image.assert_not_called()

    @patch("raster.views.tiles._get_singleband_image")
    def test_unknown_tile_source_returns_not_found(
        self,
        mock_get_singleband_image,
    ):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/tiles/raster/unknown/a/b/3/1/2.png")

        self.assertEqual(response.status_code, 404)
        mock_get_singleband_image.assert_not_called()


class RasterTileSourceViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="source-user",
            password="testpass",
        )
        self.access_group = Group.objects.create(name="source-access")
        self.user.groups.add(self.access_group)
        dataset = Dataset.objects.create(
            id="land_cover",
            label="Land Cover",
            group="exposure",
            unit="class",
            stacking_order=1,
            display_order=1,
        )
        dataset.access_groups.add(self.access_group)
        self.source = RasterTileSource.objects.create(
            domain="land_cover",
            name="Land Cover",
            group="Exposure",
            description="Land cover tiles",
            license="CC-BY",
            keys=["region", "year"],
            database="terracotta_land_cover",
            dataset=dataset,
        )

    def test_sources_requires_authentication(self):
        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 403)

    def test_lists_tile_sources(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["domain"], "land_cover")

    def test_returns_single_tile_source(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/tiles/raster/sources/{self.source.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.source.pk)

    @patch("raster.views.sources._source_options")
    def test_returns_source_domains(
        self,
        mock_source_options,
    ):
        self.client.force_authenticate(user=self.user)
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
        mock_source_options.assert_called_once_with(
            "terracotta_land_cover", filters=None
        )

    @patch("raster.views.sources._source_options")
    def test_filters_source_domains_by_terracotta_type(
        self,
        mock_source_options,
    ):
        self.client.force_authenticate(user=self.user)
        dataset = Dataset.objects.create(
            id="coastal",
            label="Coastal",
            group="hazards",
            unit="m",
            stacking_order=2,
            display_order=2,
        )
        dataset.access_groups.add(self.access_group)
        RasterTileSource.objects.create(
            domain="coastal",
            name="Coastal",
            group="Hazards",
            database="terracotta.sqlite",
            keys=["type", "rp", "rcp", "epoch", "confidence"],
            dataset=dataset,
        )
        mock_source_options.return_value = []

        response = self.client.get(
            "/tiles/raster/sources/coastal/domains"
        )

        self.assertEqual(response.status_code, 200)
        mock_source_options.assert_called_once_with(
            "terracotta.sqlite", filters={"type": "coastal"}
        )

    @patch("raster.views.sources._source_options")
    def test_restricted_source_is_hidden_from_all_source_routes(
        self,
        mock_source_options,
    ):
        dataset = self.source.dataset
        dataset.access_groups.clear()
        dataset.access_groups.add(Group.objects.create(name="restricted"))
        self.client.force_authenticate(user=self.user)

        list_response = self.client.get("/tiles/raster/sources")
        detail_response = self.client.get(
            f"/tiles/raster/sources/{self.source.pk}"
        )
        domains_response = self.client.get(
            "/tiles/raster/sources/land_cover/domains"
        )

        self.assertEqual(list_response.json(), [])
        self.assertEqual(detail_response.status_code, 403)
        self.assertEqual(domains_response.status_code, 403)
        self.assertEqual(
            detail_response.json()["detail"],
            "You do not have permission to access this raster source.",
        )
        self.assertEqual(
            domains_response.json()["detail"],
            "You do not have permission to access this raster source.",
        )
        mock_source_options.assert_not_called()

    def test_group_member_can_access_restricted_source(self):
        access_group = Group.objects.create(name="restricted")
        dataset = self.source.dataset
        dataset.access_groups.clear()
        dataset.access_groups.add(access_group)
        self.user.groups.add(access_group)
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["domain"], "land_cover")

    def test_unlinked_source_is_hidden(self):
        unlinked = RasterTileSource.objects.create(
            domain="legacy",
            name="Legacy",
            group="Exposure",
            keys=["region", "year"],
        )
        self.client.force_authenticate(user=self.user)

        list_response = self.client.get("/tiles/raster/sources")
        detail_response = self.client.get(
            f"/tiles/raster/sources/{unlinked.pk}"
        )

        self.assertEqual(
            [source["domain"] for source in list_response.json()],
            ["land_cover"],
        )
        self.assertEqual(detail_response.status_code, 403)

    def test_unknown_source_returns_not_found(self):
        self.client.force_authenticate(user=self.user)

        detail_response = self.client.get("/tiles/raster/sources/999999")
        domains_response = self.client.get(
            "/tiles/raster/sources/unknown/domains"
        )

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(domains_response.status_code, 404)
