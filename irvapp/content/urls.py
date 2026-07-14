from django.urls import path

from content.views import MarkdownBlockPageView


urlpatterns = [
    path(
        "<slug:page>",
        MarkdownBlockPageView.as_view(),
        name="markdown-block-page"
    ),
]
