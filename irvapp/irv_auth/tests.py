from unittest.mock import patch

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class AuthRouteTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=True,
        )

    def _csrf_token(self):
        self.client.get("/auth/me")
        return self.client.cookies["csrftoken"].value

    def test_me_returns_anonymous_session_and_sets_csrf_cookie(self):
        response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"authenticated": False, "user": None},
        )
        self.assertIn("csrftoken", response.cookies)

    def test_login_authenticates_user_session(self):
        response = self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"},
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["authenticated"], True)
        self.assertEqual(
            response.json()["user"],
            {
                "id": self.user.id,
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
            },
        )

        current_user_response = self.client.get("/auth/me")
        self.assertEqual(current_user_response.status_code, 200)
        self.assertEqual(
            current_user_response.json()["user"]["username"],
            "testuser",
        )

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid username or password."},
        )

    def test_login_rejects_unverified_email(self):
        EmailAddress.objects.filter(user=self.user).update(verified=False)

        response = self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"},
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": "Please verify your email address before logging in."},
        )

        current_user_response = self.client.get("/auth/me")
        self.assertEqual(
            current_user_response.json(),
            {"authenticated": False, "user": None},
        )

    def test_logout_clears_authenticated_session(self):
        self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"},
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        response = self.client.post(
            "/auth/logout",
            format="json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"authenticated": False, "user": None},
        )

    @patch("allauth.account.models.EmailAddress.send_confirmation")
    def test_register_creates_user_and_email_address(self, mock_send):
        password = "not-common-enough-12345"
        response = self.client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "detail": (
                    "Registration successful. Please check your email "
                    "to verify your account before logging in."
                )
            },
        )

        new_user = User.objects.get(username="newuser")
        self.assertEqual(new_user.email, "new@example.com")
        self.assertTrue(new_user.check_password(password))

        email_address = EmailAddress.objects.get(user=new_user)
        self.assertEqual(email_address.email, "new@example.com")
        self.assertEqual(email_address.primary, True)
        self.assertEqual(email_address.verified, False)
        mock_send.assert_called_once()

    def test_register_rejects_invalid_payload(self):
        response = self.client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "not-an-email",
                "password": "testpass123",
            },
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid registration details."},
        )

    def test_register_rejects_password_that_fails_policy(self):
        response = self.client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password",
            },
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_rejects_duplicate_user(self):
        response = self.client.post(
            "/auth/register",
            data={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "testpass123",
            },
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf_token(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "This account is already registered."},
        )
