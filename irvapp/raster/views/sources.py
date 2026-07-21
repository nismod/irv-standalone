import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Dataset
from api.permissions import HasDatasetAccess

from ..internal.helpers import handle_exception
from ..models import RasterTileSource
from ..serializers import (
    RasterTileSourceDomainsSerializer,
    RasterTileSourceSerializer,
)
from .shared import _source_options

logger = logging.getLogger(__name__)

class RasterTileSourceListView(APIView):
    permission_classes = [IsAuthenticated, HasDatasetAccess]

    @extend_schema(
        operation_id="raster_tile_sources",
        responses={200: RasterTileSourceSerializer(many=True)},
    )
    def get(self, request):
        try:
            sources = RasterTileSource.objects.visible_to(request.user)
            serializer = RasterTileSourceSerializer(sources, many=True)
            return Response(serializer.data)
        except Exception as err:
            handle_exception(logger, err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RasterTileSourceDetailView(APIView):
    permission_classes = [IsAuthenticated, HasDatasetAccess]

    @extend_schema(
        operation_id="raster_tile_source",
        responses={
            200: RasterTileSourceSerializer,
            403: OpenApiResponse(description="Raster source access denied."),
            404: OpenApiResponse(description="Raster source not found."),
        },
    )
    def get(self, request, source_id):
        try:
            source = RasterTileSource.objects.get(pk=source_id)
            self.check_object_permissions(request, source)
            serializer = RasterTileSourceSerializer(source)
            return Response(serializer.data)
        except RasterTileSource.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied:
            raise
        except Exception as err:
            handle_exception(logger, err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RasterTileSourceDomainsView(APIView):
    permission_classes = [IsAuthenticated, HasDatasetAccess]

    @extend_schema(
        operation_id="raster_tile_source_domains",
        responses={
            200: RasterTileSourceDomainsSerializer,
            403: OpenApiResponse(description="Access denied."),
            404: OpenApiResponse(description="Not found."),
        },
    )
    def get(self, request, dataset_id):
        try:
            dataset = Dataset.objects.select_related("tile_source").get(
                pk=dataset_id
            )
            self.check_object_permissions(request, dataset)
            source = dataset.tile_source
            if source is None:
                raise RasterTileSource.DoesNotExist
            filters = (
                {"type": dataset_id} if "type" in source.keys else None
            )
            domains = _source_options(source.database, filters=filters)
            serializer = RasterTileSourceDomainsSerializer(
                {"domains": domains}
            )
            return Response(serializer.data)
        except (Dataset.DoesNotExist, RasterTileSource.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied:
            raise
        except Exception as err:
            handle_exception(logger, err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
