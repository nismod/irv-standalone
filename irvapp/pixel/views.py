import os
from functools import lru_cache
from typing import NamedTuple

import pandas as pd
from pathlib import Path
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from pyproj import CRS
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .query import point_query, RasterStackMetadata
from .serializers import PixelDataSerializer


def read_grid_metadata(target_path: Path) -> list[RasterStackMetadata]:
    datasets = pd.read_csv(target_path / "stacks.csv")
    return [
        RasterStackMetadata(
            ds.grid_id,
            target_path / ds.fname,
            CRS(ds.crs)
        )
        for ds in datasets.itertuples()
    ]


class PixelMetadataUnavailable(Exception):
    pass


class PixelMetadata(NamedTuple):
    grid_metadata: list[RasterStackMetadata]
    layer_metadata: pd.DataFrame


@lru_cache(maxsize=1)
def get_pixel_metadata() -> PixelMetadata:
    data_path = Path(os.getenv("PIXEL_STACK_DATA_DIR", "/data"))
    layer_metadata_path = os.getenv("LAYER_METADATA_PATH")

    if not layer_metadata_path:
        raise PixelMetadataUnavailable("LAYER_METADATA_PATH is not set.")

    stacks_path = data_path / "stacks.csv"
    if not stacks_path.exists():
        raise PixelMetadataUnavailable(
            f"Pixel stack metadata not found at {stacks_path}."
        )

    layer_path = Path(layer_metadata_path)
    if not layer_path.exists():
        raise PixelMetadataUnavailable(
            f"Layer metadata not found at {layer_path}."
        )

    return PixelMetadata(
        grid_metadata=read_grid_metadata(data_path),
        layer_metadata=pd.read_csv(layer_path),
    )


class PointQueryView(APIView):
    serializer_class = PixelDataSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="lon",
                type=OpenApiTypes.DOUBLE,
                location=OpenApiParameter.PATH,
                description="Longitude in EPSG:4326.",
                required=True,
            ),
            OpenApiParameter(
                name="lat",
                type=OpenApiTypes.DOUBLE,
                location=OpenApiParameter.PATH,
                description="Latitude in EPSG:4326.",
                required=True,
            ),
        ],
        responses=PixelDataSerializer,
    )
    def get(self, request, lon, lat):
        errors = {}
        lon_value = None
        lat_value = None
        try:
            lon_value = float(lon)
        except (TypeError, ValueError):
            errors["lon"] = f"Invalid longitude '{lon}'. Expected a float."
        try:
            lat_value = float(lat)
        except (TypeError, ValueError):
            errors["lat"] = f"Invalid latitude '{lat}'. Expected a float."
        if errors:
            return Response(
                {
                    "detail": "Invalid coordinate path parameter(s).",
                    "errors": errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pixel_metadata = get_pixel_metadata()
        except PixelMetadataUnavailable:
            return Response(
                {
                    "detail": "Pixel metadata is unavailable.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        pixel_data = point_query(
            pixel_metadata.grid_metadata,
            pixel_metadata.layer_metadata,
            lon_value,
            lat_value,
        )
        return Response(self.serializer_class(pixel_data).data)
