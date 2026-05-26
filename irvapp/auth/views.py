from typing import cast

from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CurrentUserSerializer, LoginRequestSerializer


class SessionStateSerializer(serializers.Serializer):
    authenticated = serializers.BooleanField()
    user = CurrentUserSerializer(allow_null=True)


def _session_payload(user):
    if user.is_authenticated:
        return {
            "authenticated": True,
            "user": CurrentUserSerializer(user).data,
        }

    return {
        "authenticated": False,
        "user": None,
    }


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginRequestSerializer,
        responses={
            200: SessionStateSerializer,
            401: OpenApiResponse(
                response=inline_serializer(
                    "LoginErrorResponse",
                    {
                        "detail": serializers.CharField(),
                    },
                ),
                description="Invalid credentials.",
            ),
            403: OpenApiResponse(
                response=inline_serializer(
                    "LoginCsrfErrorResponse",
                    {
                        "detail": serializers.CharField(),
                    },
                ),
                description="CSRF validation failed.",
            ),
        },
    )
    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, str], serializer.validated_data)

        user = authenticate(
            request,
            username=validated_data["username"],
            password=validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response(
            _session_payload(request.user),
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    @extend_schema(responses=SessionStateSerializer)
    def get(self, request):
        return Response(
            _session_payload(request.user),
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: SessionStateSerializer,
            403: OpenApiResponse(
                response=inline_serializer(
                    "LogoutCsrfErrorResponse",
                    {
                        "detail": serializers.CharField(),
                    },
                ),
                description="CSRF validation failed.",
            ),
        }
    )
    def post(self, request):
        logout(request)
        return Response(
            _session_payload(request.user),
            status=status.HTTP_200_OK,
        )
