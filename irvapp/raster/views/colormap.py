import logging
import json

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

from ..serializers import ColorMapOptionsSerializer, ColorMapSerializer
from .shared import _get_colormap

logger = logging.getLogger(__name__)


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
