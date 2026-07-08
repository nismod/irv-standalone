from django.urls import path

from .views import CurrentUserView, LoginView, LogoutView, register_view

urlpatterns = [
    path('login', LoginView.as_view()),
    path('me', CurrentUserView.as_view()),
    path('logout', LogoutView.as_view()),
    path('register', register_view),
]
