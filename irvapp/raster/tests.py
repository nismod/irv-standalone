import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.test import SimpleTestCase, TestCase
from django.utils.cache import has_vary_header
from rest_framework.test import APIClient

from map.models import Dataset
from raster import ingestion as ingest
from raster.management.commands.ingest_rasters import Command

from .internal.colormaps import CATEGORICAL_COLOR_MAPS
from .models import DEFAULT_PATH_TEMPLATE, RasterTileSource
from .views import _parse_keys, _source_options


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


class RasterTileSourceModelTests(TestCase):
    def test_path_template_defaults_from_model(self):
        source = RasterTileSource.objects.create(keys=["type", "epoch"])

        self.assertEqual(source.path_template, DEFAULT_PATH_TEMPLATE)


class SourceOptionsTests(SimpleTestCase):
    @patch("raster.views.shared.build_driver_path")
    @patch("raster.views.shared.get_settings")
    @patch("raster.views.shared.get_driver")
    def test_reads_source_options_inside_driver_connection(
        self,
        mock_get_driver,
        mock_get_settings,
        mock_build_driver_path,
    ):
        mock_build_driver_path.return_value = "/tiles/terracotta.sqlite"
        mock_get_settings.return_value.DRIVER_PROVIDER = "sqlite"
        driver = MagicMock()
        driver.get_datasets.return_value = {
            ("coastal", "100"): "/rasters/coastal.tif"
        }
        driver.get_keys.return_value = {"type": "", "rp": ""}
        mock_get_driver.return_value = driver

        options = _source_options("terracotta.sqlite")

        self.assertEqual(options, [{"type": "coastal", "rp": "100"}])
        mock_get_driver.assert_called_once_with(
            "/tiles/terracotta.sqlite",
            provider="sqlite",
        )
        driver.connect.assert_called_once_with()
        driver.connect.return_value.__enter__.assert_called_once_with()
        driver.connect.return_value.__exit__.assert_called_once()
        driver.get_datasets.assert_called_once_with(where=None)
        driver.get_keys.assert_called_once_with()

    @patch("raster.views.shared.build_driver_path")
    @patch("raster.views.shared.get_settings")
    @patch("raster.views.shared.get_driver")
    def test_passes_filters_to_terracotta_dataset_query(
        self,
        mock_get_driver,
        mock_get_settings,
        mock_build_driver_path,
    ):
        mock_build_driver_path.return_value = "/tiles/terracotta.sqlite"
        mock_get_settings.return_value.DRIVER_PROVIDER = "sqlite"
        driver = MagicMock()
        driver.get_datasets.return_value = {
            ("coastal", "100"): "/rasters/coastal.tif"
        }
        driver.get_keys.return_value = {"type": "", "rp": ""}
        mock_get_driver.return_value = driver

        filters = {"type": "coastal"}
        options = _source_options("terracotta.sqlite", filters=filters)

        self.assertEqual(options, [{"type": "coastal", "rp": "100"}])
        driver.get_datasets.assert_called_once_with(where=filters)


class IngestRasterCommandTests(TestCase):
    @patch("raster.management.commands.ingest_rasters.ingest_rasters")
    def test_ingests_each_unique_tile_source_configuration(
        self,
        mock_ingest_rasters,
    ):
        Command().handle(
            base_path="/data/raster",
            rgb_key=None,
            skip_existing=False,
            skip_metadata=False,
            quiet=True,
        )

        self.assertEqual(mock_ingest_rasters.call_count, 0)

        RasterTileSource.objects.create(
            keys=["type", "epoch"],
            database="terracotta_a.sqlite",
            path_template="hazards/{type}.tif",
        )
        RasterTileSource.objects.create(
            keys=["type", "epoch"],
            database="terracotta_a.sqlite",
            path_template="hazards/{type}.tif",
        )
        RasterTileSource.objects.create(
            keys=["type", "epoch"],
            database="terracotta_b.sqlite",
            path_template="/abs/{type}.tif",
        )

        Command().handle(
            base_path="/base",
            rgb_key="type",
            skip_existing=True,
            skip_metadata=True,
            quiet=True,
        )

        self.assertEqual(mock_ingest_rasters.call_count, 2)
        mock_ingest_rasters.assert_any_call(
            path_template="/base/hazards/{type}.tif",
            database="/base/terracotta_a.sqlite",
            database_provider=None,
            rgb_key="type",
            skip_existing=True,
            skip_metadata=True,
            quiet=True,
        )
        mock_ingest_rasters.assert_any_call(
            path_template="/abs/{type}.tif",
            database="/base/terracotta_b.sqlite",
            database_provider=None,
            rgb_key="type",
            skip_existing=True,
            skip_metadata=True,
            quiet=True,
        )


class RasterTileImageViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tile-user",
            password="testpass",
        )
        self.access_group = Group.objects.create(name="tile-access")
        self.user.groups.add(self.access_group)
        land_cover_source = RasterTileSource.objects.create(
            keys=["region", "year"],
            database="terracotta_land_cover",
        )
        aqueduct_source = RasterTileSource.objects.create(
            keys=["region", "year"],
            database="terracotta_aqueduct",
        )
        land_cover_dataset = Dataset.objects.create(
            id="land_cover",
            label="Land Cover",
            group="exposure",
            unit="class",
            tile_source=land_cover_source,
            stacking_order=1,
            display_order=1,
        )
        land_cover_dataset.access_groups.add(self.access_group)
        aqueduct_dataset = Dataset.objects.create(
            id="aqueduct",
            label="Aqueduct",
            group="hazards",
            unit="m",
            tile_source=aqueduct_source,
            stacking_order=2,
            display_order=2,
        )
        aqueduct_dataset.access_groups.add(self.access_group)

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
        self.assertEqual(response.content, b"png-bytes")
        self.assertEqual(response["Cache-Control"], "private, max-age=60")
        self.assertTrue(has_vary_header(response, "Cookie"))
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
    def test_invalid_stretch_range_returns_bad_request(
        self,
        mock_get_singleband_image,
    ):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/tiles/raster/land_cover/a/b/3/1/2.png?stretch_range=not-json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "Invalid JSON in tile query parameters.",
        )
        mock_get_singleband_image.assert_not_called()

    @patch("raster.views.tiles._get_singleband_image")
    def test_restricted_tile_is_not_rendered_for_non_member(
        self,
        mock_get_singleband_image,
    ):
        source = Dataset.objects.get(pk="land_cover").tile_source
        dataset = source.datasets.get()
        dataset.access_groups.clear()
        dataset.access_groups.add(Group.objects.create(name="restricted"))
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/tiles/raster/land_cover/a/b/3/1/2.png"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "You do not have permission to access this dataset.",
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

    @patch("raster.views.tiles._get_singleband_image")
    def test_dataset_without_tile_source_returns_not_found(
        self,
        mock_get_singleband_image,
    ):
        dataset = Dataset.objects.create(
            id="vector_only",
            label="Vector only",
            group="networks",
            unit="n/a",
            stacking_order=3,
            display_order=3,
        )
        dataset.access_groups.add(self.access_group)
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/tiles/raster/vector_only/a/b/3/1/2.png"
        )

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
        self.source = RasterTileSource.objects.create(
            description="Land cover tiles",
            keys=["region", "year"],
            database="terracotta_land_cover",
        )
        self.dataset = Dataset.objects.create(
            id="land_cover",
            label="Land Cover",
            group="exposure",
            unit="class",
            license="CC-BY",
            tile_source=self.source,
            stacking_order=1,
            display_order=1,
        )
        self.dataset.access_groups.add(self.access_group)

    def test_sources_requires_authentication(self):
        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 403)

    def test_lists_tile_sources(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], self.source.pk)
        self.assertNotIn("domain", response.json()[0])
        self.assertNotIn("name", response.json()[0])
        self.assertNotIn("group", response.json()[0])
        self.assertNotIn("license", response.json()[0])

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
        source = RasterTileSource.objects.create(
            database="terracotta.sqlite",
            keys=["type", "rp", "rcp", "epoch", "confidence"],
        )
        dataset = Dataset.objects.create(
            id="coastal",
            label="Coastal",
            group="hazards",
            unit="m",
            tile_source=source,
            stacking_order=2,
            display_order=2,
        )
        dataset.access_groups.add(self.access_group)
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
        dataset = self.dataset
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
            "You do not have permission to access this dataset.",
        )
        mock_source_options.assert_not_called()

    @patch("raster.views.sources._source_options")
    def test_dataset_without_tile_source_returns_not_found(
        self,
        mock_source_options,
    ):
        dataset = Dataset.objects.create(
            id="vector_only",
            label="Vector only",
            group="networks",
            unit="n/a",
            stacking_order=2,
            display_order=2,
        )
        dataset.access_groups.add(self.access_group)
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/tiles/raster/sources/vector_only/domains"
        )

        self.assertEqual(response.status_code, 404)
        mock_source_options.assert_not_called()

    def test_group_member_can_access_restricted_source(self):
        access_group = Group.objects.create(name="restricted")
        dataset = self.dataset
        dataset.access_groups.clear()
        dataset.access_groups.add(access_group)
        self.user.groups.add(access_group)
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], self.source.pk)

    def test_tile_source_can_serve_multiple_datasets(self):
        second_dataset = Dataset.objects.create(
            id="land_cover_change",
            label="Land Cover Change",
            group="exposure",
            unit="class",
            tile_source=self.source,
            stacking_order=2,
            display_order=2,
        )
        second_dataset.access_groups.add(self.access_group)
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/tiles/raster/sources")

        self.assertEqual(self.source.datasets.count(), 2)
        self.assertEqual(len(response.json()), 1)

    @patch("raster.views.sources._source_options")
    def test_shared_source_does_not_bypass_dataset_access(
        self,
        mock_source_options,
    ):
        restricted = Dataset.objects.create(
            id="restricted_land_cover",
            label="Restricted Land Cover",
            group="exposure",
            unit="class",
            tile_source=self.source,
            stacking_order=2,
            display_order=2,
        )
        restricted.access_groups.add(
            Group.objects.create(name="other-source-access")
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/tiles/raster/sources/restricted_land_cover/domains"
        )

        self.assertEqual(response.status_code, 403)
        mock_source_options.assert_not_called()

    def test_unlinked_source_is_hidden(self):
        unlinked = RasterTileSource.objects.create(
            keys=["region", "year"],
        )
        self.client.force_authenticate(user=self.user)

        list_response = self.client.get("/tiles/raster/sources")
        detail_response = self.client.get(
            f"/tiles/raster/sources/{unlinked.pk}"
        )

        self.assertEqual(
            [source["id"] for source in list_response.json()],
            [self.source.pk],
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
