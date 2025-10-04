from __future__ import annotations

from django.core import mail
from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User


class AuthenticationTests(APITestCase):
    def _register_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "user@example.com",
                "first_name": "Jan",
                "last_name": "Kowalski",
                "phone_number": "+48 123 456 789",
                "pesel": "90010112345",
                "role": User.UserRole.ENTITY_ADMIN,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)
        return response

    def test_register_sends_activation_email(self):
        response = self._register_user()
        payload = response.data
        user = User.objects.get(email="user@example.com")

        self.assertIn("detail", payload)
        self.assertEqual(user.pesel_masked, "*******2345")
        self.assertFalse(user.is_active)
        self.assertTrue(user.must_change_password)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("activate", mail.outbox[0].body)

    def test_activation_enables_login(self):
        self._register_user()
        user = User.objects.get(email="user@example.com")

        activation_link = next(line for line in mail.outbox[0].body.splitlines() if line.startswith("http"))
        from urllib.parse import parse_qs, urlparse

        params = parse_qs(urlparse(activation_link).query)
        uid = params["uid"][0]
        token = params["token"][0]

        activation_response = self.client.post(
            reverse("activate"),
            {
                "uid": uid,
                "token": token,
                "password": "StrongPassword!123",
                "password_confirm": "StrongPassword!123",
            },
        )

        self.assertEqual(activation_response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(user.must_change_password)

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "user@example.com",
                "password": "StrongPassword!123",
            },
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("token", login_response.data)
