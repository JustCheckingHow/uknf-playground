# Generated manually to provide initial schema for accounts app
from __future__ import annotations

import django.contrib.auth.models
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import migrations, models
import django.utils.timezone

import accounts.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("username", models.CharField(blank=True, max_length=150, verbose_name="username")),
                (
                    "first_name",
                    models.CharField(blank=True, max_length=150, verbose_name="first name"),
                ),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="adres e-mail")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("system_admin", "Administrator systemu"),
                            ("supervisor", "Nadzorca"),
                            ("analyst", "Analityk"),
                            ("communication_officer", "Koordynator komunikacji"),
                            ("auditor", "Audytor"),
                            ("entity_admin", "Administrator podmiotu"),
                            ("submitter", "Osoba raportująca"),
                            ("representative", "Przedstawiciel"),
                            ("read_only", "Tylko podgląd"),
                        ],
                        default="entity_admin",
                        max_length=64,
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        validators=[RegexValidator(r"^[0-9+ ]*$", "Niepoprawny numer telefonu")],
                    ),
                ),
                ("department", models.CharField(blank=True, max_length=128)),
                ("position_title", models.CharField(blank=True, max_length=128)),
                ("preferred_language", models.CharField(default="pl", max_length=16)),
                ("must_change_password", models.BooleanField(default=False)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
            managers=[
                ("objects", accounts.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="RegulatedEntity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("registration_number", models.CharField(max_length=64, unique=True)),
                ("sector", models.CharField(max_length=64)),
                ("address", models.CharField(max_length=255)),
                ("postal_code", models.CharField(max_length=16)),
                ("city", models.CharField(max_length=128)),
                ("country", models.CharField(default="PL", max_length=64)),
                ("contact_email", models.EmailField(max_length=254)),
                ("contact_phone", models.CharField(max_length=32)),
                ("website", models.URLField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Aktywny"),
                            ("suspended", "Zawieszony"),
                            ("decommissioned", "Wycofany"),
                        ],
                        default="active",
                        max_length=32,
                    ),
                ),
                ("data_source", models.CharField(blank=True, max_length=128)),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="AccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entity_name", models.CharField(max_length=255)),
                ("entity_registration_number", models.CharField(blank=True, max_length=64)),
                ("requester_name", models.CharField(max_length=255)),
                ("requester_email", models.EmailField(max_length=254)),
                ("requester_phone", models.CharField(blank=True, max_length=32)),
                ("requested_role", models.CharField(max_length=64)),
                ("justification", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("submitted", "Złożony"),
                            ("under_review", "W trakcie analizy"),
                            ("approved", "Zatwierdzony"),
                            ("rejected", "Odrzucony"),
                        ],
                        default="submitted",
                        max_length=32,
                    ),
                ),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("decision_notes", models.TextField(blank=True)),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="processed_access_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ContactSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sender_name", models.CharField(max_length=255)),
                ("sender_email", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("handled_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_notes", models.TextField(blank=True)),
                (
                    "entity",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to="accounts.regulatedentity"),
                ),
                (
                    "handled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="handled_contact_messages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EntityMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin", "Administrator"),
                            ("submitter", "Osoba raportująca"),
                            ("representative", "Przedstawiciel"),
                            ("viewer", "Odczyt"),
                        ],
                        max_length=32,
                    ),
                ),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "entity",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="memberships", to="accounts.regulatedentity"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="memberships", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notify_via_email", models.BooleanField(default=True)),
                ("notify_via_sms", models.BooleanField(default=False)),
                ("daily_digest", models.BooleanField(default=True)),
                ("weekly_digest", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(on_delete=models.CASCADE, related_name="notification_preferences", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserSessionContext",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "acting_entity",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to="accounts.regulatedentity"),
                ),
                (
                    "user",
                    models.OneToOneField(on_delete=models.CASCADE, related_name="session_context", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="entitymembership",
            constraint=models.UniqueConstraint(fields=("user", "entity", "role"), name="accounts_entitymembership_unique"),
        ),
    ]
