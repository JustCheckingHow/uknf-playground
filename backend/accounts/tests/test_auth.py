from __future__ import annotations

from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User


class AuthenticationTests(APITestCase):
    def test_register_and_login(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "user@example.com",
                "password": "StrongPassword!123",
                "first_name": "Jan",
                "last_name": "Kowalski",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)

        response = self.client.post(
            reverse("login"),
            {
                "email": "user@example.com",
                "password": "StrongPassword!123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
