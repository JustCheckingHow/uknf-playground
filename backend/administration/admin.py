from __future__ import annotations

from django.contrib import admin

from .models import AuditLogEntry, DataRetentionPolicy, MaintenanceWindow, PasswordPolicy


@admin.register(PasswordPolicy)
class PasswordPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "min_length",
        "require_uppercase",
        "require_lowercase",
        "require_numbers",
        "require_special",
        "password_expiry_days",
        "updated_at",
    )


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "severity")
    list_filter = ("severity",)
    search_fields = ("action", "metadata")


@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ("data_type", "retention_period_days", "updated_at")


@admin.register(MaintenanceWindow)
class MaintenanceWindowAdmin(admin.ModelAdmin):
    list_display = ("title", "start_time", "end_time", "created_by")

