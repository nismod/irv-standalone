from urllib.error import URLError
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient


class _FakeUpstreamResponse:
    def __init__(self, *, status, body, headers):
        self.status = status
        self._body = body
        self.headers = headers
        self._offset = 0
        self.closed = False

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def geturl(self):
        return "http://raster-tileserver:5000/singleband/a/1/b/2/c/3/4.png"

    def read(self, size=-1):
        if size is None or size < 0:
            size = len(self._body) - self._offset

        if self._offset >= len(self._body):
            return b""

        end = min(self._offset + size, len(self._body))
        chunk = self._body[self._offset:end]
        self._offset = end
        return chunk

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@override_settings(
    RASTER_TILESERVER_INTERNAL_URL="http://raster-tileserver:5000"
)
class RasterTileProxyViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tile-user",
            password="testpass",
        )

    def test_requires_authentication(self):
        response = self.client.get(
            "/tiles/raster/singleband/a/1/b/2/c/3/4.png"
        )

        self.assertEqual(response.status_code, 403)

    @patch("raster_proxy.views.build_opener")
    def test_proxies_raster_tile_response_for_authenticated_user(
        self,
        mock_build_opener,
    ):
        self.client.force_authenticate(user=self.user)
        fake_response = _FakeUpstreamResponse(
            status=200,
            body=b"png-bytes",
            headers={
                "Content-Type": "image/png",
                "Cache-Control": "public, max-age=60",
                "ETag": '"abc123"',
            },
        )
        opener = MagicMock()
        opener.open.return_value = fake_response
        mock_build_opener.return_value = opener

        response = self.client.get(
            (
                "/tiles/raster/singleband/a/1/b/2/c/3/4.png"
                "?colormap=viridis"
            ),
            HTTP_ACCEPT="*/*",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"png-bytes")
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "public, max-age=60")
        self.assertEqual(response["ETag"], '"abc123"')
        self.assertTrue(fake_response.closed)

        forwarded_request = opener.open.call_args.args[0]
        self.assertEqual(
            forwarded_request.full_url,
            (
                "http://raster-tileserver:5000/"
                "singleband/a/1/b/2/c/3/4.png?colormap=viridis"
            ),
        )
        self.assertEqual(forwarded_request.get_method(), "GET")
        self.assertEqual(
            forwarded_request.get_header("Accept"),
            "*/*",
        )

    @patch("raster_proxy.views.build_opener")
    def test_returns_503_when_upstream_is_unavailable(
        self, mock_build_opener
    ):
        self.client.force_authenticate(user=self.user)
        opener = MagicMock()
        opener.open.side_effect = URLError("down")
        mock_build_opener.return_value = opener

        response = self.client.get(
            "/tiles/raster/singleband/a/1/b/2/c/3/4.png"
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Raster tile service is currently unavailable.",
        )

    @patch("raster_proxy.views.colormap")
    def test_colormap_endpoint(self, mock_colormap):
        self.client.force_authenticate(user=self.user)
        mock_colormap.return_value = [
            {"value": 0, "rgba": [0, 0, 0, 255]},
            {"value": 1, "rgba": [1, 1, 1, 255]},
        ]

        response = self.client.get("/tiles/raster/colormap?colormap=viridis")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {
            "colormap": [
                {"value": 0, "rgba": [0, 0, 0, 255]},
                {"value": 1, "rgba": [1, 1, 1, 255]},
            ]
        })

        mock_colormap.assert_called_once_with(
            colormap="viridis",
            stretch_range=[0, 255],
            num_values=255,
        )

    @patch("raster_proxy.views.colormap")
    def test_colormap_endpoint_passes_through_stretch_range(
        self,
        mock_colormap,
    ):
        self.client.force_authenticate(user=self.user)
        mock_colormap.return_value = []

        response = self.client.get(
            "/tiles/raster/colormap"
            "?colormap=viridis&stretch_range=[10,20]"
        )

        self.assertEqual(response.status_code, 200)
        mock_colormap.assert_called_once_with(
            colormap="viridis",
            stretch_range=[10.0, 20.0],
            num_values=255,
        )

    @patch("raster_proxy.views.build_opener")
    def test_head_does_not_include_response_body(self, mock_build_opener):
        self.client.force_authenticate(user=self.user)
        fake_response = _FakeUpstreamResponse(
            status=200,
            body=b"png-bytes",
            headers={
                "Content-Type": "image/png",
            },
        )
        opener = MagicMock()
        opener.open.return_value = fake_response
        mock_build_opener.return_value = opener

        response = self.client.head(
            "/tiles/raster/singleband/a/1/b/2/c/3/4.png"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(fake_response.closed)

        forwarded_request = opener.open.call_args.args[0]
        self.assertEqual(forwarded_request.get_method(), "HEAD")
        self.assertEqual(
            forwarded_request.full_url,
            "http://raster-tileserver:5000/singleband/a/1/b/2/c/3/4.png",
        )
