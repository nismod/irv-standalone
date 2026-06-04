from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from api.models import MapConfig


class MapConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapConfig
        fields = ['config_name', 'config_value']


class MapConfigViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = MapConfig.objects.all()
    serializer_class = MapConfigSerializer