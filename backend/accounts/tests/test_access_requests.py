from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import (
    AccessRequest,
    EntityMembership,
    RegulatedEntity,
    User,
)


class AccessRequestWorkflowTests(APITestCase):
    def setUp(self):
        self.entity = RegulatedEntity.objects.create(
            name="Test Entity",
            registration_number="ENT-001",
            sector="Banking",
            address="Main St 1",
            postal_code="00-001",
            city="Warsaw",
            country="PL",
            contact_email="entity@example.com",
            contact_phone="48111222333",
        )
        self.entity_admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminStrong!1",
            first_name="Anna",
            last_name="Admin",
            role=User.UserRole.ENTITY_ADMIN,
        )
        EntityMembership.objects.create(
            user=self.entity_admin,
            entity=self.entity,
            role=EntityMembership.MembershipRole.ADMIN,
            is_primary=True,
        )

    def _register_and_activate(self, *, email: str, role: str) -> User:
        mail.outbox.clear()
        register_response = self.client.post(
            reverse("register"),
            {
                "email": email,
                "first_name": "Piotr",
                "last_name": "Nowak",
                "phone_number": "+48 500 600 700",
                "pesel": "85010112345",
                "role": role,
            },
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)

        activation_link = next(line for line in mail.outbox[0].body.splitlines() if line.startswith("http"))
        params = parse_qs(urlparse(activation_link).query)
        activation_response = self.client.post(
            reverse("activate"),
            {
                "uid": params["uid"][0],
                "token": params["token"][0],
                "password": "StrongPassword!1",
                "password_confirm": "StrongPassword!1",
            },
        )
        self.assertEqual(activation_response.status_code, status.HTTP_200_OK)
        return User.objects.get(email=email)

    def test_submit_and_approve_request_flow(self):
        submitter = self._register_and_activate(email="user@example.com", role=User.UserRole.SUBMITTER)
        request_record = AccessRequest.objects.get(requester=submitter)
        self.assertEqual(request_record.status, AccessRequest.AccessStatus.DRAFT)

        self.client.force_authenticate(user=submitter)
        update_response = self.client.patch(
            reverse("access-request-detail", args=[request_record.pk]),
            {
                "justification": "Potrzebuję dostępu do raportowania",
                "lines": [
                    {
                        "entity_id": self.entity.pk,
                        "permission_codes": [
                            "reporting",
                        ],
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        request_record.refresh_from_db()
        self.assertEqual(request_record.lines.count(), 1)
        line = request_record.lines.first()
        self.assertEqual(list(line.permissions.values_list("code", flat=True)), ["reporting"])

        submit_response = self.client.post(reverse("access-request-submit", args=[request_record.pk]))
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        request_record.refresh_from_db()
        self.assertEqual(request_record.status, AccessRequest.AccessStatus.NEW)
        self.assertEqual(request_record.next_actor, AccessRequest.NextActor.ENTITY_ADMIN)
        self.assertEqual(len(mail.outbox), 2)  # activation + submission confirmation

        self.client.force_authenticate(user=self.entity_admin)
        approve_response = self.client.post(
            reverse("access-request-approve-line", kwargs={"pk": request_record.pk, "line_id": line.pk}),
            {"notes": "Akceptacja przez administratora"},
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        request_record.refresh_from_db()
        self.assertEqual(request_record.status, AccessRequest.AccessStatus.APPROVED)
        membership_exists = EntityMembership.objects.filter(
            user=submitter,
            entity=self.entity,
            role=EntityMembership.MembershipRole.SUBMITTER,
        ).exists()
        self.assertTrue(membership_exists)

    def test_entity_admin_permission_requires_uknf(self):
        submitter = self._register_and_activate(email="admin-candidate@example.com", role=User.UserRole.ENTITY_ADMIN)
        request_record = AccessRequest.objects.get(requester=submitter)

        self.client.force_authenticate(user=submitter)
        self.client.patch(
            reverse("access-request-detail", args=[request_record.pk]),
            {
                "lines": [
                    {
                        "entity_id": self.entity.pk,
                        "permission_codes": ["entity_admin"],
                    }
                ],
            },
            format="json",
        )
        self.client.post(reverse("access-request-submit", args=[request_record.pk]))
        request_record.refresh_from_db()
        line = request_record.lines.first()

        self.client.force_authenticate(user=self.entity_admin)
        deny_response = self.client.post(
            reverse("access-request-approve-line", kwargs={"pk": request_record.pk, "line_id": line.pk}),
        )
        self.assertEqual(deny_response.status_code, status.HTTP_403_FORBIDDEN)

        supervisor = User.objects.create_user(
            email="uknf@example.com",
            password="Supervisor!1",
            role=User.UserRole.SYSTEM_ADMIN,
        )
        self.client.force_authenticate(user=supervisor)
        approve_response = self.client.post(
            reverse("access-request-approve-line", kwargs={"pk": request_record.pk, "line_id": line.pk}),
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        request_record.refresh_from_db()
        self.assertEqual(request_record.status, AccessRequest.AccessStatus.APPROVED)
        self.assertTrue(request_record.handled_by_uknf)
