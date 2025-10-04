from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class PasswordPolicy(models.Model):
    min_length = models.PositiveIntegerField(default=12)
    require_uppercase = models.BooleanField(default=True)
    require_lowercase = models.BooleanField(default=True)
    require_numbers = models.BooleanField(default=True)
    require_special = models.BooleanField(default=True)
    password_expiry_days = models.PositiveIntegerField(default=90)
    reuse_history = models.PositiveIntegerField(default=5)
    lockout_threshold = models.PositiveIntegerField(default=5)
    lockout_duration_minutes = models.PositiveIntegerField(default=15)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return "PasswordPolicy"


class AuditLogEntry(models.Model):
    class Severity(models.TextChoices):
        INFO = "info", "Informacja"
        WARNING = "warning", "Ostrzeżenie"
        ERROR = "error", "Błąd"
        CRITICAL = "critical", "Krytyczne"

    action = models.CharField(max_length=255)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.INFO)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.created_at} {self.action}"

    @classmethod
    def record(cls, *, actor=None, action: str, metadata: dict | None = None, severity: str | None = None, request=None) -> "AuditLogEntry":
        entry = cls(
            actor=actor,
            action=action,
            metadata=metadata or {},
            severity=severity or cls.Severity.INFO,
        )
        if request:
            entry.ip_address = request.META.get("REMOTE_ADDR")
            entry.user_agent = request.META.get("HTTP_USER_AGENT", "")
        entry.save()
        return entry


class DataRetentionPolicy(models.Model):
    data_type = models.CharField(max_length=128, unique=True)
    retention_period_days = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"RetentionPolicy({self.data_type})"


class MaintenanceWindow(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-start_time"]

    def is_active(self) -> bool:
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def __str__(self) -> str:  # pragma: no cover
        return self.title
