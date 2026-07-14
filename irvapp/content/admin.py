from django.contrib import admin

from content.models import Logo, MarkdownBlock


@admin.register(MarkdownBlock)
class MarkdownBlockAdmin(admin.ModelAdmin):
    list_display = ["title", "page", "slot"]
    list_filter = ["page"]
    search_fields = ["title", "markdown"]

    class Media:
        css = {"all": ("content/admin.css",)}


@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ["name", "page", "slot", "position", "height"]
    list_editable = ["position"]
    list_filter = ["page", "slot"]
    search_fields = ["name", "link"]
