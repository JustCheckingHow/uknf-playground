from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="managed_entities",
            field=models.ManyToManyField(blank=True, related_name="managed_by", to="accounts.regulatedentity"),
        ),
        migrations.DeleteModel(
            name="AccessRequest",
        ),
        migrations.CreateModel(
            name="AccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference_code", models.CharField(editable=False, max_length=24, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Roboczy"),
                            ("new", "Nowy"),
                            ("approved", "Zaakceptowany"),
                            ("blocked", "Zablokowany"),
                            ("updated", "Zaktualizowany"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                (
                    "next_actor",
                    models.CharField(
                        choices=[
                            ("requester", "Wnioskodawca"),
                            ("entity_admin", "Administrator podmiotu"),
                            ("uknf", "UKNF"),
                            ("none", "Brak"),
                        ],
                        default="requester",
                        max_length=32,
                    ),
                ),
                ("handled_by_uknf", models.BooleanField(default=False)),
                ("requester_first_name", models.CharField(max_length=150)),
                ("requester_last_name", models.CharField(max_length=150)),
                ("requester_email", models.EmailField(max_length=254)),
                ("requester_phone", models.CharField(blank=True, max_length=32)),
                ("requester_pesel", models.CharField(blank=True, max_length=11)),
                ("justification", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("decision_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "decided_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="decided_access_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AccessRequestAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="access_requests/attachments/%Y/%m/%d")),
                ("description", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "request",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="accounts.accessrequest"),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AccessRequestHistoryEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=64)),
                (
                    "from_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("draft", "Roboczy"),
                            ("new", "Nowy"),
                            ("approved", "Zaakceptowany"),
                            ("blocked", "Zablokowany"),
                            ("updated", "Zaktualizowany"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("draft", "Roboczy"),
                            ("new", "Nowy"),
                            ("approved", "Zaakceptowany"),
                            ("blocked", "Zablokowany"),
                            ("updated", "Zaktualizowany"),
                        ],
                        max_length=32,
                    ),
                ),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="history", to="accounts.accessrequest"),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="AccessRequestLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Oczekujące"),
                            ("approved", "Zaakceptowane"),
                            ("blocked", "Zablokowane"),
                            ("needs_update", "Wymaga aktualizacji"),
                        ],
                        default="pending",
                        max_length=32,
                    ),
                ),
                (
                    "next_actor",
                    models.CharField(
                        choices=[
                            ("requester", "Wnioskodawca"),
                            ("entity_admin", "Administrator podmiotu"),
                            ("uknf", "UKNF"),
                            ("none", "Brak"),
                        ],
                        default="entity_admin",
                        max_length=32,
                    ),
                ),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("decision_notes", models.TextField(blank=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "decided_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="decided_access_request_lines",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "entity",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="access_request_lines", to="accounts.regulatedentity"),
                ),
                (
                    "request",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="accounts.accessrequest"),
                ),
            ],
            options={"unique_together": {("request", "entity")}},
        ),
        migrations.CreateModel(
            name="AccessRequestMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("is_internal", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "request",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="accounts.accessrequest"),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="AccessRequestMessageAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="access_requests/messages/%Y/%m/%d")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "message",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="accounts.accessrequestmessage"),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AccessRequestLinePermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "code",
                    models.CharField(
                        choices=[
                            ("reporting", "Sprawozdawczość"),
                            ("cases", "Sprawy"),
                            ("entity_admin", "Administrator podmiotu"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("requested", "Wnioskowane"),
                            ("granted", "Przyznane"),
                            ("blocked", "Zablokowane"),
                        ],
                        default="requested",
                        max_length=16,
                    ),
                ),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "decided_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="decided_access_request_permissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "line",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="permissions", to="accounts.accessrequestline"),
                ),
            ],
            options={"unique_together": {("line", "code")}},
        ),
    ]
