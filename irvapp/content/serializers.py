from rest_framework import serializers

from content.models import MarkdownBlock


class MarkdownBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkdownBlock
        fields = ["slot", "markdown"]
