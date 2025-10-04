from __future__ import annotations

from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import EntityMembership
from accounts.permissions import IsEntityMember, IsInternalUser
from administration.models import AuditLogEntry
from .models import (
    Announcement,
    AnnouncementAcknowledgement,
    Case,
    FaqEntry,
    LibraryDocument,
    MessageThread,
    Report,
)
from .serializers import (
    AnnouncementAcknowledgeSerializer,
    AnnouncementSerializer,
    CaseSerializer,
    FaqEntrySerializer,
    LibraryDocumentSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    MessageThreadSerializer,
    ReportSerializer,
    ReportStatusSerializer,
)


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related("entity", "submitted_by").prefetch_related("timeline")
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["entity", "status", "report_type"]
    ordering_fields = ["submitted_at", "validated_at", "created_at"]
    search_fields = ["title", "entity__name", "report_type"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_internal:
            return qs
        entity_ids = EntityMembership.objects.filter(user=self.request.user).values_list("entity_id", flat=True)
        return qs.filter(entity_id__in=entity_ids)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalUser])
    def status(self, request, *args, **kwargs):
        report = self.get_object()
        serializer = ReportStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report.set_status(serializer.validated_data["status"], message=serializer.validated_data.get("notes"))
        report.timeline.create(
            status=report.status,
            created_by=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        AuditLogEntry.record(
            actor=request.user,
            action="report.status_change",
            metadata={"report_id": report.pk, "status": report.status},
        )
        return Response(ReportSerializer(report).data)

    @action(detail=True, methods=["post"], permission_classes=[IsEntityMember])
    def submit(self, request, *args, **kwargs):
        report = self.get_object()
        report.mark_submitted(request.user)
        report.timeline.create(
            status=report.status,
            created_by=request.user,
            notes="Sprawozdanie przesłane przez użytkownika",
        )
        AuditLogEntry.record(actor=request.user, action="report.submitted", metadata={"report_id": report.pk})
        return Response(ReportSerializer(report).data)


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.select_related("entity", "assigned_to").prefetch_related("timeline")
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "entity"]
    search_fields = ["reference_code", "title", "entity__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_internal:
            return qs
        entity_ids = EntityMembership.objects.filter(user=self.request.user).values_list("entity_id", flat=True)
        return qs.filter(entity_id__in=entity_ids)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsInternalUser()]
        return super().get_permissions()


class MessageThreadViewSet(viewsets.ModelViewSet):
    queryset = MessageThread.objects.select_related("entity", "created_by").prefetch_related("participants", "messages")
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_internal:
            return qs
        entity_ids = EntityMembership.objects.filter(user=self.request.user).values_list("entity_id", flat=True)
        return qs.filter(Q(entity_id__in=entity_ids) | Q(participants=self.request.user)).distinct()

    def perform_create(self, serializer):
        thread = serializer.save()
        AuditLogEntry.record(actor=self.request.user, action="thread.created", metadata={"thread_id": thread.pk})

    @action(detail=True, methods=["get", "post"], permission_classes=[IsAuthenticated])
    def messages(self, request, *args, **kwargs):
        thread = self.get_object()
        if request.method == "GET":
            messages = thread.messages.select_related("sender")
            return Response(MessageSerializer(messages, many=True).data)
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = thread.add_message(
            sender=request.user,
            content=serializer.validated_data["body"],
            attachments=serializer.validated_data.get("attachments"),
            is_internal_note=serializer.validated_data.get("is_internal_note", False),
        )
        AuditLogEntry.record(
            actor=request.user,
            action="thread.message",
            metadata={"thread_id": thread.pk, "message_id": message.pk},
        )
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.select_related("created_by").prefetch_related("acknowledgements")
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["requires_acknowledgement"]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsInternalUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        announcement = serializer.save(created_by=self.request.user)
        AuditLogEntry.record(actor=self.request.user, action="announcement.published", metadata={"id": announcement.pk})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def acknowledge(self, request, *args, **kwargs):
        announcement = self.get_object()
        serializer = AnnouncementAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        acknowledgement, _ = AnnouncementAcknowledgement.objects.update_or_create(
            announcement=announcement,
            user=request.user,
            defaults={"acknowledged": serializer.validated_data.get("acknowledged", True)},
        )
        AuditLogEntry.record(
            actor=request.user,
            action="announcement.acknowledge",
            metadata={"announcement_id": announcement.pk, "acknowledged": acknowledgement.acknowledged},
        )
        return Response(AnnouncementSerializer(announcement).data)


class LibraryDocumentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = LibraryDocument.objects.all().order_by("-published_at")
    serializer_class = LibraryDocumentSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["category", "is_mandatory"]


class FaqViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = FaqEntry.objects.filter(is_active=True).order_by("order")
    serializer_class = FaqEntrySerializer
    permission_classes = [AllowAny]
