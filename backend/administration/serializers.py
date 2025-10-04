from __future__ import annotations

from rest_framework import serializers

from .models import AuditLogEntry, DataRetentionPolicy, MaintenanceWindow, PasswordPolicy


class PasswordPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordPolicy
        fields = [
            "id",
            "min_length",
            "require_uppercase",
            "require_lowercase",
            "require_numbers",
            "require_special",
            "password_expiry_days",
            "reuse_history",
            "lockout_threshold",
            "lockout_duration_minutes",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditLogEntry
        fields = ["id", "action", "actor_email", "severity", "metadata", "ip_address", "user_agent", "created_at"]


class DataRetentionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataRetentionPolicy
        fields = ["id", "data_type", "retention_period_days", "description", "updated_at"]
        read_only_fields = ["updated_at"]


class MaintenanceWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceWindow
        fields = ["id", "title", "description", "start_time", "end_time", "created_at", "created_by"]
        read_only_fields = ["created_at", "created_by"]
