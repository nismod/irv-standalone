import json
import logging

from django.http import StreamingHttpResponse
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
from terracotta.exceptions import DatasetNotFoundError

from ..internal.colormaps import CATEGORICAL_COLOR_MAPS
from ..internal.helpers import handle_exception
from .shared import (
    MissingExplicitColourMapException,
    SourceDBDoesNotExistException,
    _get_singleband_image,
    _parse_keys,
    _tile_db_from_domain,
    get_image_size,
)

logger = logging.getLogger(__name__)


class RasterTileImageView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="colormap",
                description=(
                    "Colormap name to use for rendering the tile. Set to "
                    '"explicit" for categorical data.'
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="stretch_range",
                description=(
                    "Optional stretch range as a JSON array, e.g. [0, 10]."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="explicit_color_map",
                description=(
                    "JSON categorical map used when colormap=explicit."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Rendered raster tile response."),
            400: OpenApiResponse(description="Invalid tile parameters."),
            500: OpenApiResponse(
                description="Unexpected tile rendering error."
            ),
        },
    )
    def get(self, request, domain="", keys="", tile_z=0, tile_x=0, tile_y=0):
        parsed_keys = []
        source_db = "unknown"

        stretch_range = request.query_params.get("stretch_range")
        explicit_color_map = request.query_params.get("explicit_color_map")
        colormap_name = request.query_params.get("colormap")

        stretch_range_log = stretch_range
        if stretch_range:
            try:
                stretch_range_log = json.loads(stretch_range)
            except json.JSONDecodeError:
                pass

        logger.debug(
            (
                "tile path %s, colormap: %s, stretch_range: %s, "
                "explicit_color_map: %s"
            ),
            keys,
            colormap_name,
            stretch_range_log if stretch_range_log else "",
            explicit_color_map,
        )

        try:
            parsed_keys = _parse_keys(keys)
            source_db = _tile_db_from_domain(domain)
            logger.debug("source DB for tile path: %s", source_db)

            options = {}
            if colormap_name:
                if colormap_name == "explicit":
                    if domain in CATEGORICAL_COLOR_MAPS.keys():
                        options["colormap"] = CATEGORICAL_COLOR_MAPS[domain]
                    elif not explicit_color_map:
                        raise MissingExplicitColourMapException()
                    else:
                        options["colormap"] = json.loads(explicit_color_map)
                else:
                    options["colormap"] = colormap_name

            if stretch_range:
                options["stretch_range"] = json.loads(stretch_range)

            logger.debug(
                "db %s keys %s tile %s options %s",
                source_db,
                parsed_keys,
                [tile_x, tile_y, tile_z],
                options,
            )
            image = _get_singleband_image(
                source_db,
                parsed_keys,
                [tile_x, tile_y, tile_z],
                options,
            )
            logger.debug(
                "tile image of size returned: %s, %s",
                get_image_size(image),
                type(image),
            )

            return StreamingHttpResponse(image, content_type="image/png")
        except json.JSONDecodeError as err:
            handle_exception(logger, err)
            return Response(
                {"detail": "Invalid JSON in tile query parameters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as err:
            handle_exception(logger, err)
            return Response(
                {"detail": str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MissingExplicitColourMapException as err:
            handle_exception(logger, err)
            return Response(
                {
                    "detail": (
                        "colormap=explicit requires explicit_color_map to be "
                        "included"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SourceDBDoesNotExistException as err:
            handle_exception(logger, err)
            return Response(
                {
                    "detail": (
                        "source database for domain"
                        f"{err.source_db} does not exist in "
                        "tiles metastore"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DatasetNotFoundError as err:
            handle_exception(logger, err)
            return Response(
                {
                    "detail": (
                        f"layer with keys {parsed_keys} not found in "
                        f"{source_db} in tiles metastore"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as err:
            handle_exception(logger, err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
