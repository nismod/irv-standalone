from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from api.models import InfrastructureNode


class InfrastructureNodeSerializer(serializers.ModelSerializer):

    def get_fields(self):
        fields = super(InfrastructureNodeSerializer, self).get_fields()
        fields['children'] = InfrastructureNodeSerializer(
            many=True,
            read_only=True,
            context=self.context,
        )
        return fields
    class Meta:
        model = InfrastructureNode
        fields = ['node_id', 'node_name', 'parent', 'children']



class InfrastructureNodeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InfrastructureNodeSerializer

    def get_queryset(self):
        queryset = InfrastructureNode.objects.all()
        if self.action == "list":
            return queryset.filter(parent=None)
        return queryset
