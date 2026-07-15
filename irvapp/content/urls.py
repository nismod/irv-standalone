from django.urls import path

from content.views import LogoPageView, MarkdownBlockPageView, PageView


urlpatterns = [
    path(
        "<slug:page>/logos",
        LogoPageView.as_view(),
        name="logo-page",
    ),
    path(
        "<slug:page>/metadata",
        PageView.as_view(),
        name="page-metadata",
    ),
    path(
        "<slug:page>",
        MarkdownBlockPageView.as_view(),
        name="markdown-block-page",
    ),
]
