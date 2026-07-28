import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from map.models import Dataset
from map.permissions import user_has_dataset_access
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class VectorTileProxyView(APIView):
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

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Proxied vector tile response."),
            304: OpenApiResponse(description="Not modified."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Permission denied."),
            502: OpenApiResponse(
                description="Invalid upstream redirect target."
            ),
            503: OpenApiResponse(
                description="Vector tile upstream service unavailable."
            ),
        }
    )
    def get(self, request, tile_path=""):
        return self._proxy_request(request, tile_path)

    @extend_schema(exclude=True)
    def head(self, request, tile_path=""):
        return self._proxy_request(request, tile_path)

    def _proxy_request(self, request, tile_path):
        self._check_vector_data_access(request, tile_path)
        upstream_url = self._build_upstream_url(request, tile_path)
        include_body = request.method != "HEAD"
        upstream_request = Request(
            upstream_url,
            method=request.method,
            headers=self._build_forward_headers(request),
        )

        try:
            with urlopen(upstream_request, timeout=10) as upstream_response:
                resolved_url = upstream_response.geturl()
                if not self._is_allowed_upstream_url(resolved_url):
                    return Response(
                        {
                            "detail": (
                                "Vector tile upstream returned an invalid "
                                "redirect target."
                            )
                        },
                        status=status.HTTP_502_BAD_GATEWAY,
                    )
                response_body = (
                    upstream_response.read() if include_body else b""
                )
                return self._build_django_response(
                    status_code=upstream_response.status,
                    upstream_headers=upstream_response.headers,
                    body=self._rewrite_json_urls(
                        request=request,
                        tile_path=tile_path,
                        upstream_headers=upstream_response.headers,
                        body=response_body,
                    ),
                )
        except HTTPError as exc:
            resolved_url = exc.geturl()
            if not self._is_allowed_upstream_url(resolved_url):
                return Response(
                    {
                        "detail": (
                            "Vector tile upstream returned an invalid "
                            "redirect target."
                        )
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            response_body = exc.read() if include_body else b""
            return self._build_django_response(
                status_code=exc.code,
                upstream_headers=exc.headers,
                body=self._rewrite_json_urls(
                    request=request,
                    tile_path=tile_path,
                    upstream_headers=exc.headers,
                    body=response_body,
                ),
            )
        except URLError:
            return Response(
                {
                    "detail": (
                        "Vector tile service is currently unavailable."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def _check_vector_data_access(self, request, tile_path):
        dataset_id = self._dataset_id_from_tile_path(tile_path)
        if dataset_id is None:
            return

        if request.user.is_superuser:
            return

        dataset = (
            Dataset.objects.prefetch_related("access_groups")
            .filter(pk=dataset_id)
            .first()
        )
        user_group_ids = set(request.user.groups.values_list("pk", flat=True))
        if not user_has_dataset_access(
            request.user,
            dataset,
            user_group_ids=user_group_ids,
        ):
            raise PermissionDenied(
                "You do not have permission to access this dataset."
            )

    def _dataset_id_from_tile_path(self, tile_path):
        path_parts = tile_path.lstrip("/").split("/")
        if len(path_parts) < 2 or path_parts[0] != "data":
            return None

        dataset_path_part = path_parts[1]
        if "." in dataset_path_part:
            dataset_path_part = dataset_path_part.rsplit(".", 1)[0]

        return dataset_path_part or None

    def _is_allowed_upstream_url(self, url_value):
        resolved = urlsplit(url_value)
        expected = urlsplit(settings.VECTOR_TILESERVER_INTERNAL_URL)
        return resolved.hostname == expected.hostname

    def _build_upstream_url(self, request, tile_path):
        base_url = settings.VECTOR_TILESERVER_INTERNAL_URL.rstrip("/")
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

    def _build_django_response(self, status_code, upstream_headers, body):
        response = HttpResponse(content=body, status=status_code)
        if upstream_headers is None:
            return response

        for header_name in self._response_headers_to_forward:
            header_value = upstream_headers.get(header_name)
            if header_value:
                response[header_name] = header_value
        return response

    def _rewrite_json_urls(self, request, tile_path, upstream_headers, body):
        if not body or upstream_headers is None:
            return body

        content_type = upstream_headers.get("Content-Type", "")
        if "json" not in content_type.lower():
            return body

        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return body

        rewritten_payload = self._rewrite_payload_urls(
            payload,
            proxy_root=self._build_proxy_root_path(request, tile_path),
        )
        if rewritten_payload == payload:
            return body

        return json.dumps(rewritten_payload).encode("utf-8")

    def _build_proxy_root_path(self, request, tile_path):
        request_path = request.path
        normalized_tile_path = tile_path.lstrip("/")

        if (
            normalized_tile_path
            and request_path.endswith(normalized_tile_path)
        ):
            proxy_path = request_path[: -len(normalized_tile_path)]
        else:
            proxy_path = request_path

        forwarded_prefix = request.META.get(
            "HTTP_X_FORWARDED_PREFIX", ""
        ).rstrip("/")
        if forwarded_prefix and not proxy_path.startswith(
            f"{forwarded_prefix}/"
        ):
            proxy_path = f"{forwarded_prefix}{proxy_path}"

        return f"{proxy_path.rstrip('/')}/"

    def _rewrite_payload_urls(self, value, proxy_root):
        if isinstance(value, dict):
            return {
                key: self._rewrite_payload_urls(item, proxy_root)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                self._rewrite_payload_urls(item, proxy_root)
                for item in value
            ]
        if isinstance(value, str):
            return self._rewrite_vector_tileserver_url(value, proxy_root)
        return value

    def _rewrite_vector_tileserver_url(self, url_value, proxy_root):
        parsed = urlsplit(url_value)
        relative_path = None

        if parsed.path.startswith("/vector/"):
            relative_path = parsed.path[len("/vector/"):]
        elif parsed.path.startswith("/data/"):
            relative_path = parsed.path.lstrip("/")

        if not relative_path:
            return url_value

        if parsed.netloc:
            upstream_host = urlsplit(
                settings.VECTOR_TILESERVER_INTERNAL_URL
            ).hostname
            allowed_hosts = {
                "localhost",
                "127.0.0.1",
                upstream_host,
            }
            if parsed.hostname not in allowed_hosts:
                return url_value

        rewritten_url = urljoin(proxy_root, relative_path)
        rewritten_parts = urlsplit(rewritten_url)
        return urlunsplit(
            (
                rewritten_parts.scheme,
                rewritten_parts.netloc,
                rewritten_parts.path,
                parsed.query,
                parsed.fragment,
            )
        )
