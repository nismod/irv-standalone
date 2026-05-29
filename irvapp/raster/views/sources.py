import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..internal.helpers import handle_exception
from ..models import RasterTileSource
from ..serializers import (
    RasterTileSourceDomainsSerializer,
    RasterTileSourceSerializer,
)
from .shared import (
    SourceDBDoesNotExistException,
    _source_options,
    _tile_db_from_domain,
)

logger = logging.getLogger(__name__)


class RasterTileSourceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="raster_tile_sources",
        responses={200: RasterTileSourceSerializer(many=True)},
    )
    def get(self, request):
        try:
            sources = RasterTileSource.objects.all()
            serializer = RasterTileSourceSerializer(sources, many=True)
            return Response(serializer.data)
        except Exception as err:
            handle_exception(logger, err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RasterTileSourceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="raster_tile_source",
        responses={200: RasterTileSourceSerializer},
    )
    def get(self, request, source_id):
        try:
            source = RasterTileSource.objects.get(pk=source_id)
            serializer = RasterTileSourceSerializer(source)
            return Response(serializer.data)
        except RasterTileSource.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as err:
            handle_exception(logger, err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RasterTileSourceDomainsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="raster_tile_source_domains",
        responses={200: RasterTileSourceDomainsSerializer},
    )
    def get(self, request, source_id):
        try:
            source = RasterTileSource.objects.get(pk=source_id)
            domains = _source_options(_tile_db_from_domain(source.domain))
            serializer = RasterTileSourceDomainsSerializer(
                {"domains": domains}
            )
            return Response(serializer.data)
        except RasterTileSource.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except SourceDBDoesNotExistException as err:
            handle_exception(logger, err)
            return Response(
                {
                    "detail": (
                        f"source database for domain {err.source_db} does not "
                        "exist in tiles metastore"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as err:
            handle_exception(logger, err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
