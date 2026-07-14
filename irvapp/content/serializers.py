from rest_framework import serializers

from content.models import Logo, MarkdownBlock


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
