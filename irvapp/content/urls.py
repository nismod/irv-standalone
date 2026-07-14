from django.urls import path

from content.views import LogoPageView, MarkdownBlockPageView


urlpatterns = [
    path(
        "<slug:page>/logos",
        LogoPageView.as_view(),
        name="logo-page",
    ),
    path(
        "<slug:page>",
        MarkdownBlockPageView.as_view(),
        name="markdown-block-page"
    ),
]
