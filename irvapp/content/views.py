from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from content.models import Logo, MarkdownBlock
from content.serializers import LogoSerializer, MarkdownBlockSerializer


class MarkdownBlockPageView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MarkdownBlockSerializer
    pagination_class = None

    def get_queryset(self):
        return MarkdownBlock.objects.filter(page=self.kwargs["page"])


class LogoPageView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = LogoSerializer
    pagination_class = None

    def get_queryset(self):
        return Logo.objects.filter(page=self.kwargs["page"])
