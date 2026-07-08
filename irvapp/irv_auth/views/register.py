from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from typing import cast

from ..serializers import RegistrationRequestSerializer

User = get_user_model()


@extend_schema(
    request=RegistrationRequestSerializer,
    responses={
        200: inline_serializer(
            "RegistrationSuccessResponse",
            {
                "detail": serializers.CharField(),
            },
        ),
        400: OpenApiResponse(
            response=inline_serializer(
                "RegistrationErrorResponse",
                {
                    "detail": serializers.CharField(),
                },
            ),
            description="Invalid registration details.",
        ),
        403: OpenApiResponse(
            response=inline_serializer(
                "RegistrationCsrfErrorResponse",
                {
                    "detail": serializers.CharField(),
                },
            ),
            description="CSRF validation failed.",
        ),
        500: OpenApiResponse(
            response=inline_serializer(
                "RegistrationFailureResponse",
                {
                    "detail": serializers.CharField(),
                },
            ),
            description="Registration failed.",
        ),
    },
)
@ensure_csrf_cookie
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegistrationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"detail": "Invalid registration details."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_data = cast(dict[str, str], serializer.validated_data)
    password = validated_data["password"]
    email = validated_data["email"]
    username = validated_data["username"]

    if not email or password is None:
        return Response(
            {"detail": "Please provide an email address and password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user_exists = User.objects.filter(username=username).exists()
    email_exists = (
        User.objects.filter(email__iexact=email).exists()
        or EmailAddress.objects.filter(email__iexact=email).exists()
    )
    if email_exists or user_exists:
        return Response(
            {"detail": "This account is already registered."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User(username=username, email=email)
    try:
        validate_password(password, user=user)
    except ValidationError as e:
        return Response(
            {"password": e.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Create the new user. The user is created up front but cannot log in
        # until their email address has been verified (enforced in login_view).
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )

        # Register the email with allauth as unverified and send the
        # confirmation email containing the verify link.
        email_address, _ = EmailAddress.objects.get_or_create(
            user=user,
            email=email,
            defaults={"primary": True, "verified": False},
        )
        email_address.send_confirmation(request, signup=True)

        return Response(
            {
                "detail": "Registration successful. Please check your email "
                "to verify your account before logging in."
            }
        )

    except Exception:
        return Response(
            {"detail": "Registration failed."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
