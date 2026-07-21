from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from content.models import Logo, MarkdownBlock, Page


class PageSerializer(serializers.ModelSerializer):
    background_image = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = [
            "name",
            "title",
            "background_image",
            "background_credit",
        ]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_background_image(self, page):
        if not page.background_image:
            return None
        return page.background_image.url


class MarkdownBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkdownBlock
        fields = ["slot", "markdown"]


class LogoSerializer(serializers.ModelSerializer):
    src = serializers.URLField(source="image.url", read_only=True)
    href = serializers.URLField(source="link")
    alt = serializers.CharField(source="name")

    class Meta:
        model = Logo
        fields = ["slot", "src", "href", "alt", "height"]
