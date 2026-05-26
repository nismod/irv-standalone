from urllib.error import URLError
from unittest.mock import patch

from django.conf import settings

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient


class _FakeUpstreamResponse:
    def __init__(self, *, status, body, headers):
        self.status = status
        self._body = body
        self.headers = headers

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def geturl(self):
        return "http://tileserver.internal:8080/data/roads.json"

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@override_settings(
    VECTOR_TILESERVER_INTERNAL_URL="http://tileserver.internal:8080"
)
class VectorTileProxyViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tile-user",
            password="testpass",
        )

    def test_requires_authentication(self):
        response = self.client.get("/tiles/vector/data/roads.json")

        self.assertEqual(response.status_code, 403)

    @patch("vector_proxy.views.urlopen")
    def test_proxies_vector_tile_response_for_authenticated_user(
        self,
        mock_urlopen,
    ):
        self.client.force_authenticate(user=self.user)
        mock_urlopen.return_value = _FakeUpstreamResponse(
            status=200,
            body=b'{"ok":true}',
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "public, max-age=60",
                "ETag": '"abc123"',
            },
        )

        response = self.client.get(
            "/tiles/vector/data/roads.json?v=2",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"ok":true}')
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response["Cache-Control"], "public, max-age=60")
        self.assertEqual(response["ETag"], '"abc123"')

        forwarded_request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            forwarded_request.full_url,
            "http://tileserver.internal:8080/data/roads.json?v=2",
        )
        self.assertEqual(forwarded_request.get_method(), "GET")
        self.assertEqual(
            forwarded_request.get_header("Accept"),
            "application/json",
        )

    @patch("vector_proxy.views.urlopen", side_effect=URLError("down"))
    def test_returns_503_when_upstream_is_unavailable(self, _mock_urlopen):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/tiles/vector/data/roads.json")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Vector tile service is currently unavailable.",
        )

    @patch("vector_proxy.views.urlopen")
    def test_rewrites_tilejson_urls_to_proxy_endpoint(self, mock_urlopen):
        self.client.force_authenticate(user=self.user)
        mock_urlopen.return_value = _FakeUpstreamResponse(
            status=200,
            body=(
                b'{"tiles":['
                b'"http://localhost/vector/data/'
                b'rail_stations/{z}/{x}/{y}.pbf"],'
                b'"data":['
                b'"http://localhost/vector/data/'
                b'rail_stations.json?secure=true"],'
                b'"attribution":"https://example.com/credits"}'
            ),
            headers={
                "Content-Type": "application/json",
            },
        )

        response = self.client.get("/tiles/vector/data/rail_stations.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        body = response.json()
        expected_prefix = "/tiles/vector/"
        self.assertEqual(
            body["tiles"][0],
            f"{expected_prefix}data/rail_stations/{{z}}/{{x}}/{{y}}.pbf",
        )
        self.assertEqual(
            body["data"][0],
            f"{expected_prefix}data/rail_stations.json?secure=true",
        )
        self.assertEqual(body["attribution"], "https://example.com/credits")

        forwarded_request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            forwarded_request.full_url,
            (
                f"{settings.VECTOR_TILESERVER_INTERNAL_URL}"
                "/data/rail_stations.json"
            ),
        )

    @patch("vector_proxy.views.urlopen")
    def test_rewrites_tilejson_urls_with_forwarded_prefix(self, mock_urlopen):
        self.client.force_authenticate(user=self.user)
        mock_urlopen.return_value = _FakeUpstreamResponse(
            status=200,
            body=(
                b'{"tiles":['
                b'"http://localhost/vector/data/'
                b'buildings_resort/{z}/{x}/{y}.pbf"]}'
            ),
            headers={
                "Content-Type": "application/json",
            },
        )

        response = self.client.get(
            "/tiles/vector/data/buildings_resort.json",
            HTTP_X_FORWARDED_PREFIX="/api",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["tiles"][0],
            "/api/tiles/vector/data/buildings_resort/{z}/{x}/{y}.pbf",
        )
