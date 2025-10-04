from __future__ import annotations

import json

from pathlib import Path

from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserGroup
from accounts.serializers import RegulatedEntitySerializer, UserSerializer
from .models import (
    Announcement,
    AnnouncementAcknowledgement,
    Case,
    CaseTimelineEntry,
    FaqEntry,
    LibraryDocument,
    Message,
    MessageThread,
    Report,
    ReportTimelineEntry,
)

User = get_user_model()


class ReportTimelineSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = ReportTimelineEntry
        fields = ["id", "status", "notes", "created_at", "created_by"]


class ReportSerializer(serializers.ModelSerializer):
    entity = RegulatedEntitySerializer(read_only=True)
    entity_id = serializers.IntegerField(write_only=True)
    submitted_by = UserSerializer(read_only=True)
    timeline = ReportTimelineSerializer(many=True, read_only=True)
    validation = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "entity",
            "entity_id",
            "submitted_by",
            "title",
            "report_type",
            "period_start",
            "period_end",
            "status",
            "submitted_at",
            "validated_at",
            "validation_errors",
            "file_path",
            "comments",
            "timeline",
            "created_at",
            "updated_at",
            "validation",
        ]
        read_only_fields = [
            "status",
            "submitted_at",
            "validated_at",
            "validation_errors",
            "timeline",
            "submitted_by",
            "created_at",
            "updated_at",
            "file_path",
            "validation",
        ]

    def create(self, validated_data):
        entity_id = validated_data.pop("entity_id")
        request = self.context["request"]
        report = Report.objects.create(entity_id=entity_id, submitted_by=request.user, **validated_data)
        if request.user:
            ReportTimelineEntry.objects.create(
                report=report,
                status=Report.ReportStatus.DRAFT,
                created_by=request.user,
                notes="Utworzono szkic sprawozdania.",
            )
        return report

    def get_validation(self, obj: Report):
        payload = obj.validation_errors
        if not payload:
            return None
        try:
            return json.loads(payload)
        except (TypeError, ValueError):
            return {"raw": payload}


class ReportStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Report.ReportStatus.choices)
    notes = serializers.CharField(required=False, allow_blank=True)


class CaseTimelineSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = CaseTimelineEntry
        fields = ["id", "status", "notes", "created_at", "created_by"]


class CaseSerializer(serializers.ModelSerializer):
    entity = RegulatedEntitySerializer(read_only=True)
    entity_id = serializers.IntegerField(write_only=True)
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    timeline = CaseTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "entity",
            "entity_id",
            "reference_code",
            "title",
            "description",
            "status",
            "assigned_to",
            "assigned_to_id",
            "due_date",
            "opened_at",
            "closed_at",
            "timeline",
            "updated_at",
        ]
        read_only_fields = ["opened_at", "closed_at", "timeline", "updated_at", "status", "assigned_to"]

    def create(self, validated_data):
        entity_id = validated_data.pop("entity_id")
        assigned_to_id = validated_data.pop("assigned_to_id", None)
        case = Case.objects.create(entity_id=entity_id, assigned_to_id=assigned_to_id, **validated_data)
        CaseTimelineEntry.objects.create(case=case, status=case.status, created_by=self.context["request"].user)
        return case


class SimpleUserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ["id", "name"]


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "thread",
            "sender",
            "recipient",
            "body",
            "attachment",
            "is_internal_note",
            "created_at",
        ]
        read_only_fields = ["thread", "sender", "recipient", "attachment", "created_at"]

    def get_attachment(self, obj: Message):
        if not obj.attachment:
            return None
        request = self.context.get("request") if hasattr(self, "context") else None
        url = obj.attachment.url
        if request is not None:
            url = request.build_absolute_uri(url)
        return {
            "url": url,
            "name": Path(obj.attachment.name).name,
        }


class MessageCreateSerializer(serializers.ModelSerializer):
    attachment = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Message
        fields = ["body", "attachment", "is_internal_note"]


class MessageThreadSerializer(serializers.ModelSerializer):
    entity = RegulatedEntitySerializer(read_only=True)
    entity_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by = UserSerializer(read_only=True)
    participants = UserSerializer(read_only=True, many=True)
    messages = MessageSerializer(many=True, read_only=True)
    target_group = SimpleUserGroupSerializer(read_only=True)
    target_group_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    target_user = SimpleUserSerializer(read_only=True)
    target_user_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = MessageThread
        fields = [
            "id",
            "entity",
            "entity_id",
            "subject",
            "created_by",
            "is_internal_only",
            "is_global",
            "target_group",
            "target_group_id",
            "target_user",
            "target_user_id",
            "participants",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "created_by",
            "participants",
            "messages",
            "is_global",
            "target_group",
            "target_user",
        ]

    def create(self, validated_data):
        entity_id = validated_data.pop("entity_id", None)
        target_group_id = validated_data.pop("target_group_id", None)
        target_user_id = validated_data.pop("target_user_id", None)
        thread = MessageThread.objects.create(
            entity_id=entity_id,
            target_group_id=target_group_id,
            target_user_id=target_user_id,
            created_by=self.context["request"].user,
            **validated_data,
        )
        if self.context["request"].user:
            thread.participants.add(self.context["request"].user)
        return thread


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    acknowledgement_rate = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "summary",
            "content",
            "published_at",
            "expires_at",
            "requires_acknowledgement",
            "target_roles",
            "created_by",
            "acknowledgement_rate",
        ]
        read_only_fields = ["published_at", "created_by", "acknowledgement_rate"]

    def get_acknowledgement_rate(self, obj: Announcement) -> float:
        return obj.acknowledgement_rate()


class AnnouncementAcknowledgeSerializer(serializers.Serializer):
    acknowledged = serializers.BooleanField(default=True)


class GlobalMessageBroadcastSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    target_type = serializers.ChoiceField(choices=[("group", "group"), ("user", "user")])
    group = serializers.PrimaryKeyRelatedField(queryset=UserGroup.objects.all(), required=False, allow_null=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate(self, attrs):
        target_type = attrs.get("target_type")
        if target_type == "group":
            if not attrs.get("group"):
                raise serializers.ValidationError({"group": "Wybierz grupę odbiorców."})
            attrs["user"] = None
        elif target_type == "user":
            if not attrs.get("user"):
                raise serializers.ValidationError({"user": "Wybierz użytkownika."})
            attrs["group"] = None
        else:
            raise serializers.ValidationError({"target_type": "Nieobsługiwany typ odbiorcy."})
        return attrs


class LibraryDocumentSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = LibraryDocument
        fields = [
            "id",
            "title",
            "category",
            "version",
            "published_at",
            "description",
            "document_url",
            "is_mandatory",
            "uploaded_at",
        ]

    def get_document_url(self, obj: LibraryDocument) -> str:
        resolved = obj.resolved_url
        request = self.context.get("request") if hasattr(self, "context") else None
        if resolved:
            if resolved.startswith("http"):
                return resolved
            if request is not None:
                return request.build_absolute_uri(resolved)
            return resolved
        if obj.file:
            file_url = obj.file.url
            if request is not None:
                return request.build_absolute_uri(file_url)
            return file_url
        return ""


class FaqEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqEntry
        fields = ["id", "question", "answer", "category", "order", "is_active", "updated_at"]
