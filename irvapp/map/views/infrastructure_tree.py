from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from map.models import InfrastructureTree


class InfrastructureTreeSerializer(serializers.ModelSerializer):

    def get_fields(self):
        fields = super(InfrastructureTreeSerializer, self).get_fields()
        fields['children'] = InfrastructureTreeSerializer(
            many=True,
            read_only=True,
            context=self.context,
        )
        return fields

    class Meta:
        model = InfrastructureTree
        fields = ['node_id', 'node_name', 'parent', 'feature_layer', 'children']


class InfrastructureTreeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InfrastructureTreeSerializer

    def get_queryset(self):
        queryset = InfrastructureTree.objects.all()
        if self.action == "list":
            return queryset.filter(parent=None)
        return queryset
