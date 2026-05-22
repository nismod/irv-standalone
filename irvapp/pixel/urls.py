from django.urls import path
from .views import PointQueryView

urlpatterns = [
    path("<str:lon>/<str:lat>", PointQueryView.as_view(), name="point_query"),
]
