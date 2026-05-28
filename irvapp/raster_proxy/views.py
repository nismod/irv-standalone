import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from terracotta.handlers.colormap import colormap


from .serializers import (
    ColorMapOptionsSerializer,
    ColorMapSerializer,
)


def _get_colormap(options):
    """
    Retrieve colormap
    """

    _colormap = colormap(**options)
    return ColorMapSerializer({
        "colormap": _colormap
    })


class ColormapView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="raster_colormap",
        parameters=[
            OpenApiParameter(
                name="colormap",
                description="Colormap name (e.g. 'viridis', 'plasma', etc.)",
                required=True,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="stretch_range",
                description=(
                    "Optional stretch range as a JSON array of two numbers, "
                    "e.g. [0, 100]. If not provided, the full data range "
                    "will be used."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: ColorMapSerializer,
            400: OpenApiResponse(description="Invalid colormap options."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Permission denied."),
        },
    )
    def get(self, request):
        _colormap = request.query_params.get("colormap")
        stretch_range = request.query_params.get("stretch_range")
        try:
            stretch_range_arg = (
                json.loads(stretch_range) if stretch_range else [0, 255]
            )
        except json.JSONDecodeError:
            return Response(
                {
                    "detail": (
                        "Invalid stretch_range format. Must be a JSON array "
                        "of two numbers, e.g. [0, 100]."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = ColorMapOptionsSerializer(
            data={
                "colormap": _colormap,
                "stretch_range": stretch_range_arg,
                "num_values": 255,
            }
        )
        if not options.is_valid():
            return Response(options.errors, status=status.HTTP_400_BAD_REQUEST)

        res = _get_colormap(options.validated_data)
        return Response(res.data)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class InvalidUpstreamRedirect(Exception):
    pass


class RasterTileProxyView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

    _request_headers_to_forward = (
        "Accept",
        "Accept-Encoding",
        "If-Modified-Since",
        "If-None-Match",
        "Range",
    )
    _response_headers_to_forward = (
        "Content-Type",
        "Cache-Control",
        "ETag",
        "Last-Modified",
        "Content-Encoding",
        "Accept-Ranges",
        "Content-Range",
        "Vary",
    )
    _redirect_status_codes = (301, 302, 303, 307, 308)
    _max_redirects = 5
    _stream_chunk_size = 64 * 1024

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Proxied raster tile response."),
            304: OpenApiResponse(description="Not modified."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Permission denied."),
            502: OpenApiResponse(
                description="Invalid upstream redirect target."
            ),
            503: OpenApiResponse(
                description="Raster tile upstream service unavailable."
            ),
        }
    )
    def get(self, request, tile_path=""):
        return self._proxy_request(request, tile_path)

    @extend_schema(exclude=True)
    def head(self, request, tile_path=""):
        return self._proxy_request(request, tile_path)

    def _proxy_request(self, request, tile_path):
        upstream_url = self._build_upstream_url(request, tile_path)
        if not self._is_allowed_upstream_url(upstream_url):
            return Response(
                {
                    "detail": (
                        "Raster tile upstream returned an invalid "
                        "redirect target."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        include_body = request.method != "HEAD"
        request_headers = self._build_forward_headers(request)

        try:
            upstream_response = self._open_with_validated_redirects(
                upstream_url=upstream_url,
                method=request.method,
                headers=request_headers,
                timeout=10,
            )

            if include_body:
                return self._build_django_response(
                    status_code=upstream_response.status,
                    upstream_headers=upstream_response.headers,
                    upstream_stream=upstream_response,
                )

            upstream_response.close()
            return self._build_django_response(
                status_code=upstream_response.status,
                upstream_headers=upstream_response.headers,
                body=b"",
            )
        except HTTPError as exc:
            if include_body:
                return self._build_django_response(
                    status_code=exc.code,
                    upstream_headers=exc.headers,
                    upstream_stream=exc,
                )

            exc.close()
            return self._build_django_response(
                status_code=exc.code,
                upstream_headers=exc.headers,
                body=b"",
            )
        except InvalidUpstreamRedirect:
            return Response(
                {
                    "detail": (
                        "Raster tile upstream returned an invalid "
                        "redirect target."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except URLError:
            return Response(
                {
                    "detail": (
                        "Raster tile service is currently unavailable."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def _open_with_validated_redirects(
        self, upstream_url, method, headers, timeout
    ):
        opener = build_opener(_NoRedirectHandler)
        current_url = upstream_url
        seen_urls = set()

        for _ in range(self._max_redirects + 1):
            if current_url in seen_urls:
                raise InvalidUpstreamRedirect()
            seen_urls.add(current_url)

            upstream_request = Request(
                current_url,
                method=method,
                headers=headers,
            )
            try:
                return opener.open(upstream_request, timeout=timeout)
            except HTTPError as exc:
                if exc.code not in self._redirect_status_codes:
                    raise

                location = exc.headers.get("Location")
                if not location:
                    raise InvalidUpstreamRedirect() from exc

                redirected_url = urljoin(current_url, location)
                if not self._is_allowed_upstream_url(redirected_url):
                    raise InvalidUpstreamRedirect() from exc

                exc.close()
                current_url = redirected_url

        raise InvalidUpstreamRedirect()

    def _is_allowed_upstream_url(self, url_value):
        resolved = urlsplit(url_value)
        expected = urlsplit(settings.RASTER_TILESERVER_INTERNAL_URL)
        return resolved.hostname == expected.hostname

    def _build_upstream_url(self, request, tile_path):
        base_url = settings.RASTER_TILESERVER_INTERNAL_URL.rstrip("/")
        quoted_path = quote(tile_path.lstrip("/"), safe="/")
        upstream_url = f"{base_url}/{quoted_path}" if quoted_path else base_url

        query_string = request.META.get("QUERY_STRING", "")
        if query_string:
            upstream_url = f"{upstream_url}?{query_string}"

        return upstream_url

    def _build_forward_headers(self, request):
        forward_headers = {}
        for header_name in self._request_headers_to_forward:
            header_value = request.headers.get(header_name)
            if header_value:
                forward_headers[header_name] = header_value
        return forward_headers

    def _iter_upstream_content(self, upstream_stream):
        try:
            while True:
                chunk = upstream_stream.read(self._stream_chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            upstream_stream.close()

    def _build_django_response(
        self,
        status_code,
        upstream_headers,
        body=b"",
        upstream_stream=None,
    ):
        if upstream_stream is not None:
            response = StreamingHttpResponse(
                streaming_content=self._iter_upstream_content(
                    upstream_stream
                ),
                status=status_code,
            )
        else:
            response = HttpResponse(content=body, status=status_code)

        if upstream_headers is None:
            return response

        for header_name in self._response_headers_to_forward:
            header_value = upstream_headers.get(header_name)
            if header_value:
                response[header_name] = header_value
        return response
