from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from content.models import Logo, MarkdownBlock, Page
from content.serializers import (
    LogoSerializer,
    MarkdownBlockSerializer,
    PageSerializer,
)


class PageView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PageSerializer
    queryset = Page.objects.all()
    lookup_field = "name"
    lookup_url_kwarg = "page"


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
