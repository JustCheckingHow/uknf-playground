# Generated manually to provide initial schema for communication app
from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Report",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("report_type", models.CharField(max_length=128)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Robocze"),
                            ("submitted", "Przekazane"),
                            ("processing", "W trakcie"),
                            ("validated", "Proces walidacji zakończony sukcesem"),
                            ("validation_errors", "Błędy z reguł walidacji"),
                            ("technical_failure", "Błąd techniczny w procesie"),
                            ("timeout", "Błąd – przekroczono czas"),
                            ("disputed", "Zakwestionowane przez UKNF"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                ("validation_errors", models.TextField(blank=True)),
                ("file_path", models.CharField(blank=True, max_length=512)),
                ("comments", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "entity",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="reports", to="accounts.regulatedentity"),
                ),
                (
                    "submitted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="submitted_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Case",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference_code", models.CharField(max_length=64, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Otwarte"),
                            ("in_progress", "W toku"),
                            ("responded", "Odpowiedziano"),
                            ("closed", "Zamknięte"),
                        ],
                        default="open",
                        max_length=32,
                    ),
                ),
                ("due_date", models.DateField(blank=True, null=True)),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="assigned_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "entity",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="cases", to="accounts.regulatedentity"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MessageThread",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=255)),
                ("is_internal_only", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_threads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "entity",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="message_threads", to="accounts.regulatedentity"),
                ),
                (
                    "participants",
                    models.ManyToManyField(blank=True, related_name="message_threads", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Announcement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("summary", models.CharField(max_length=512)),
                ("content", models.TextField()),
                ("published_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("requires_acknowledgement", models.BooleanField(default=False)),
                ("target_roles", models.JSONField(default=list)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="published_announcements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FaqEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.CharField(max_length=255)),
                ("answer", models.TextField()),
                ("category", models.CharField(blank=True, max_length=128)),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["order", "question"],
            },
        ),
        migrations.CreateModel(
            name="LibraryDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "title",
                    models.CharField(max_length=255),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("reporting", "Raportowanie"),
                            ("supervision", "Nadzór"),
                            ("legal", "Prawo"),
                            ("faq", "FAQ"),
                        ],
                        max_length=64,
                    ),
                ),
                ("version", models.CharField(max_length=32)),
                ("published_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("description", models.TextField()),
                ("document_url", models.URLField()),
                ("is_mandatory", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="AnnouncementAcknowledgement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("acknowledged", models.BooleanField(default=True)),
                ("acknowledged_at", models.DateTimeField(auto_now_add=True)),
                (
                    "announcement",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="acknowledgements", to="communication.announcement"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("attachments", models.JSONField(blank=True, default=list)),
                ("is_internal_note", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "sender",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "thread",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="messages", to="communication.messagethread"),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="ReportTimelineEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Robocze"),
                            ("submitted", "Przekazane"),
                            ("processing", "W trakcie"),
                            ("validated", "Proces walidacji zakończony sukcesem"),
                            ("validation_errors", "Błędy z reguł walidacji"),
                            ("technical_failure", "Błąd techniczny w procesie"),
                            ("timeout", "Błąd – przekroczono czas"),
                            ("disputed", "Zakwestionowane przez UKNF"),
                        ],
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "report",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="timeline", to="communication.report"),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="CaseTimelineEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Otwarte"),
                            ("in_progress", "W toku"),
                            ("responded", "Odpowiedziano"),
                            ("closed", "Zamknięte"),
                        ],
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "case",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="timeline", to="communication.case"),
                ),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="announcementacknowledgement",
            constraint=models.UniqueConstraint(fields=("announcement", "user"), name="communication_announcement_ack_unique"),
        ),
    ]
