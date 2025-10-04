from __future__ import annotations

from rest_framework import serializers

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


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "thread", "sender", "body", "attachments", "is_internal_note", "created_at"]
        read_only_fields = ["thread", "sender", "created_at"]


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["body", "attachments", "is_internal_note"]


class MessageThreadSerializer(serializers.ModelSerializer):
    entity = RegulatedEntitySerializer(read_only=True)
    entity_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)
    participants = UserSerializer(read_only=True, many=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = MessageThread
        fields = [
            "id",
            "entity",
            "entity_id",
            "subject",
            "created_by",
            "is_internal_only",
            "participants",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "participants", "messages"]

    def create(self, validated_data):
        entity_id = validated_data.pop("entity_id")
        thread = MessageThread.objects.create(entity_id=entity_id, created_by=self.context["request"].user, **validated_data)
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


class LibraryDocumentSerializer(serializers.ModelSerializer):
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
        ]


class FaqEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqEntry
        fields = ["id", "question", "answer", "category", "order", "is_active", "updated_at"]
