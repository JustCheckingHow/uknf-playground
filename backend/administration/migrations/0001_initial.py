# Generated manually to provide initial schema for administration app
from __future__ import annotations

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PasswordPolicy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("min_length", models.PositiveIntegerField(default=12)),
                ("require_uppercase", models.BooleanField(default=True)),
                ("require_lowercase", models.BooleanField(default=True)),
                ("require_numbers", models.BooleanField(default=True)),
                ("require_special", models.BooleanField(default=True)),
                ("password_expiry_days", models.PositiveIntegerField(default=90)),
                ("reuse_history", models.PositiveIntegerField(default=5)),
                ("lockout_threshold", models.PositiveIntegerField(default=5)),
                ("lockout_duration_minutes", models.PositiveIntegerField(default=15)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="AuditLogEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=255)),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("info", "Informacja"),
                            ("warning", "Ostrzeżenie"),
                            ("error", "Błąd"),
                            ("critical", "Krytyczne"),
                        ],
                        default="info",
                        max_length=16,
                    ),
                ),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DataRetentionPolicy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data_type", models.CharField(max_length=128, unique=True)),
                ("retention_period_days", models.PositiveIntegerField()),
                ("description", models.CharField(max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="MaintenanceWindow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-start_time"],
            },
        ),
    ]
