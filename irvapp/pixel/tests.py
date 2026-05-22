from importlib import reload
from unittest.mock import patch
from typing import cast

import math

from django.test import SimpleTestCase
from rest_framework import status

from . import views
from .serializers import PixelDataSerializer


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
