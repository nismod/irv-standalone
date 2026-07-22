from importlib import reload
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from typing import cast

import math

import numpy as np
import rasterio
from rasterio.transform import from_origin
import xarray as xr
from django.core.management import call_command
from django.test import SimpleTestCase
from rest_framework import status

from . import views
from .management.commands.ingest_pixel_stacks import Command
from .ingestion import ingest_pixel_stacks
from .serializers import PixelDataSerializer


def create_raster(file_path: Path, width: int, height: int, value: float = 0):
    transform = from_origin(0, 0, 1, 1)
    data = np.full((height, width), value, dtype=np.float32)

    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=np.float32,
        crs="EPSG:4326",
        transform=transform,
    ) as dataset:
        dataset.write(data, 1)


class PixelDataSerializerTests(SimpleTestCase):

    def test_replaces_non_finite_floats_with_none(self):
        serializer = PixelDataSerializer(
            {
                "key": ["k1", "k2", "k3"],
                "hazard": ["flood", "flood", "flood"],
                "rp": [10.0, math.nan, math.inf],
                "rcp": ["", "", ""],
                "epoch": [2030.0, -math.inf, 2050.0],
                "confidence": [math.nan, math.nan, math.nan],
                "variable": ["depth", "depth", "depth"],
                "unit": ["m", "m", "m"],
                "band_data": [1.2, math.nan, 3.4],
            }
        )

        data = cast(dict[str, list], serializer.data)

        self.assertEqual(data["rp"], [10.0, None, None])
        self.assertEqual(data["epoch"], [2030.0, None, 2050.0])
        self.assertEqual(data["band_data"], [1.2, None, 3.4])


class PixelViewMetadataTests(SimpleTestCase):

    def test_views_module_can_reload_without_pixel_metadata_env(self):
        with patch.dict(
            "os.environ",
            {"PIXEL_STACK_DATA_DIR": "", "LAYER_METADATA_PATH": ""},
            clear=False,
        ):
            reload(views)

        self.assertTrue(hasattr(views, "PointQueryView"))

    def test_point_query_returns_503_when_metadata_is_unavailable(self):
        with patch.object(
            views,
            "get_pixel_metadata",
            side_effect=views.PixelMetadataUnavailable("missing metadata"),
        ):
            response = views.PointQueryView().get(None, "1", "2")

        payload = cast(dict[str, object], response.data)
        self.assertEqual(
            response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE
        )
        self.assertEqual(payload["detail"], "Pixel metadata is unavailable.")


class PixelIngestionTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if importlib.util.find_spec("rasterio") is None:
            raise unittest.SkipTest(
                "rasterio is required for pixel ingestion tests"
            )

    def test_ingest_writes_expected_stack_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)
            source_path = temp_path / "source"
            target_path = temp_path / "target"
            layers_path = target_path / "layers-input.csv"
            source_path.mkdir()
            target_path.mkdir()

            for i, letter in enumerate(["a", "b", "c", "d"]):
                create_raster(source_path / f"{letter}.tif", 10, 10, value=i)

            layers_path.write_text(
                "path,key\n"
                "a.tif,a\n"
                "b.tif,b\n"
                "c.tif,c\n"
                "d.tif,d\n"
            )

            layers, grids = ingest_pixel_stacks(
                source_path,
                target_path,
                layers_path=layers_path,
                quiet=True,
            )

            self.assertEqual(len(layers), 4)
            self.assertEqual(len(grids), 1)

            out_file = target_path / grids.iloc[0]["fname"]
            ds = xr.open_zarr(out_file)
            self.assertEqual(ds.sizes, {"key": 4, "y": 10, "x": 10})


class PixelIngestCommandTests(SimpleTestCase):
    @patch("pixel.management.commands.ingest_pixel_stacks.ingest_pixel_stacks")
    def test_command_resolves_paths_and_calls_ingestion(
        self,
        mock_ingest_pixel_stacks,
    ):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            source_path = base_path / "source"
            target_path = base_path / "target"
            layers_path = base_path / "layers.csv"

            source_path.mkdir()
            layers_path.write_text("path,key\n")
            mock_ingest_pixel_stacks.return_value = ([], [])

            call_command(
                Command(),
                str(source_path),
                str(target_path),
                "--layers-path",
                str(layers_path),
                "--quiet",
            )

            mock_ingest_pixel_stacks.assert_called_once_with(
                source_path.resolve(),
                target_path.resolve(),
                layers_path=layers_path.resolve(),
                quiet=True,
            )
