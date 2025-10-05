"""Tests for message broadcast functionality."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserGroup
from communication.models import Message, MessageThread

User = get_user_model()


class MessageBroadcastTestCase(TestCase):
    """Test cases for message broadcast functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            role=User.UserRole.SYSTEM_ADMIN,
        )
        self.external_user = User.objects.create_user(
            email="external@test.com",
            password="testpass123",
            role=User.UserRole.SUBMITTER,
        )
        self.test_group = UserGroup.objects.create(
            name="Test Group",
            created_by=self.admin_user,
        )

    def test_broadcast_to_group_creates_thread_and_message(self):
        """Test that broadcasting to a group creates a thread with a message."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/communication/messages/broadcast/",
            {
                "subject": "Test Broadcast",
                "body": "This is a test message",
                "target_type": "group",
                "group": self.test_group.id,
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()

        # Check that the response includes the thread
        self.assertIn("id", data)
        self.assertEqual(data["subject"], "Test Broadcast")
        self.assertEqual(data["is_global"], True)
        self.assertEqual(data["target_group"]["id"], self.test_group.id)

        # Check that messages are included in the response
        self.assertIn("messages", data)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["body"], "This is a test message")

        # Verify in database
        thread = MessageThread.objects.get(id=data["id"])
        self.assertEqual(thread.subject, "Test Broadcast")
        self.assertEqual(thread.messages.count(), 1)
        self.assertEqual(thread.messages.first().body, "This is a test message")

    def test_broadcast_to_user_creates_thread_and_message(self):
        """Test that broadcasting to a specific user creates a thread with a message."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/communication/messages/broadcast/",
            {
                "subject": "Direct Message",
                "body": "This is a direct message",
                "target_type": "user",
                "user": self.external_user.id,
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()

        # Check that the response includes the thread
        self.assertIn("id", data)
        self.assertEqual(data["subject"], "Direct Message")
        self.assertEqual(data["is_global"], False)
        self.assertEqual(data["target_user"]["id"], self.external_user.id)

        # Check that messages are included in the response
        self.assertIn("messages", data)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["body"], "This is a direct message")

        # Verify in database
        thread = MessageThread.objects.get(id=data["id"])
        self.assertEqual(thread.subject, "Direct Message")
        self.assertEqual(thread.messages.count(), 1)
        self.assertEqual(thread.messages.first().body, "This is a direct message")

    def test_broadcast_requires_internal_user(self):
        """Test that only internal users can broadcast messages."""
        self.client.force_authenticate(user=self.external_user)

        response = self.client.post(
            "/api/communication/messages/broadcast/",
            {
                "subject": "Test",
                "body": "Test",
                "target_type": "group",
                "group": self.test_group.id,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_broadcast_without_group_fails(self):
        """Test that broadcasting to a group without specifying a group fails."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/communication/messages/broadcast/",
            {
                "subject": "Test",
                "body": "Test",
                "target_type": "group",
                # group is missing
            },
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("group", data)

    def test_broadcast_without_user_fails(self):
        """Test that broadcasting to a user without specifying a user fails."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/communication/messages/broadcast/",
            {
                "subject": "Test",
                "body": "Test",
                "target_type": "user",
                # user is missing
            },
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("user", data)
