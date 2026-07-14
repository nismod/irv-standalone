from django.contrib import admin

from content.models import MarkdownBlock


@admin.register(MarkdownBlock)
class MarkdownBlockAdmin(admin.ModelAdmin):
    list_display = ["title", "page", "slot"]
    list_filter = ["page"]
    search_fields = ["title", "markdown"]

    class Media:
        css = {"all": ("content/admin.css",)}
