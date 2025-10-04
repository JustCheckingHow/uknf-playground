from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
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
    GlobalMessageBroadcastSerializer,
    LibraryDocumentSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    MessageThreadSerializer,
    ReportSerializer,
    ReportStatusSerializer,
)
from .services import validate_report_workbook


logger = logging.getLogger(__name__)


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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsEntityMember],
        parser_classes=[MultiPartParser],
    )
    def upload(self, request, *args, **kwargs):
        report = self.get_object()
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Nie przesłano pliku."}, status=status.HTTP_400_BAD_REQUEST)

        storage_key = f"reports/{uuid4().hex}_{uploaded_file.name}"
        storage_path = default_storage.save(storage_key, uploaded_file)

        def cleanup_storage() -> None:
            try:
                default_storage.delete(storage_path)
            except Exception:  # pragma: no cover - cleanup best-effort
                logger.warning("Nie udało się usunąć pliku %s podczas sprzątania", storage_path)

        local_path: str | None = None
        if hasattr(default_storage, "path"):
            try:
                local_path = default_storage.path(storage_path)
            except (AttributeError, NotImplementedError):
                local_path = None

        temp_copy: Path | None = None
        if not local_path:
            temp_handle = NamedTemporaryFile(delete=False, suffix=Path(storage_path).suffix)
            with default_storage.open(storage_path, "rb") as source, open(temp_handle.name, "wb") as target:
                shutil.copyfileobj(source, target)
            temp_handle.close()
            temp_copy = Path(temp_handle.name)
            local_path = temp_copy.as_posix()

        if not local_path:
            cleanup_storage()
            return Response(
                {"detail": "Nie udało się przygotować pliku do walidacji."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            validation_result = validate_report_workbook(local_path)
        except Exception as exc:  # pragma: no cover - defensive path
            logger.exception("Walidacja sprawozdania nie powiodła się")
            cleanup_storage()
            return Response(
                {"detail": f"Błąd walidacji sprawozdania: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            if temp_copy and temp_copy.exists():
                temp_copy.unlink(missing_ok=True)

        validation_payload = validation_result.to_dict()
        has_errors = bool(validation_result.errors)
        summary = (
            f"Walidacja zakończona sukcesem. Ostrzeżenia: {len(validation_result.warnings)}."
            if not has_errors
            else f"Wykryto {len(validation_result.errors)} błędów i {len(validation_result.warnings)} ostrzeżeń."
        )

        try:
            with transaction.atomic():
                report.file_path = storage_path
                report.validation_errors = json.dumps(validation_payload, ensure_ascii=False)
                report.save(update_fields=["file_path", "validation_errors", "updated_at"])

                target_status = (
                    Report.ReportStatus.VALIDATED
                    if not has_errors
                    else Report.ReportStatus.VALIDATION_ERRORS
                )
                report.set_status(target_status, message=summary)
                report.timeline.create(
                    status=report.status,
                    created_by=request.user,
                    notes=summary,
                )

                metadata = validation_payload.get("metadata", {})
                entity_name = metadata.get("entity_name") or report.entity.name
                description_lines = [f"Podmiot: {entity_name}"]
                period_start = metadata.get("period_start")
                period_end = metadata.get("period_end")
                if period_start or period_end:
                    description_lines.append(
                        f"Okres: {period_start or 'brak'} – {period_end or 'brak'}"
                    )
                description_lines.append(
                    "Status walidacji: "
                    + ("Sukces" if target_status == Report.ReportStatus.VALIDATED else "Błędy")
                )

                LibraryDocument.objects.create(
                    title=(metadata.get("form_name") or report.title or uploaded_file.name),
                    category=LibraryDocument.DocumentCategory.REPORTING,
                    version=metadata.get("form_id") or report.report_type,
                    description="\n".join(description_lines),
                    file=storage_path,
                    content=summary,
                    is_mandatory=False,
                )
        except Exception:
            cleanup_storage()
            raise

        AuditLogEntry.record(
            actor=request.user,
            action="report.uploaded",
            metadata={
                "report_id": report.pk,
                "validation_status": validation_result.status,
                "errors": len(validation_result.errors),
                "warnings": len(validation_result.warnings),
            },
        )

        report.refresh_from_db()
        serializer = self.get_serializer(report)
        return Response(serializer.data)


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
    queryset = (
        MessageThread.objects.select_related("entity", "created_by")
        .prefetch_related("participants", "messages", "messages__sender")
        .order_by("-updated_at")
    )
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_internal:
            return qs
        entity_ids = EntityMembership.objects.filter(user=self.request.user).values_list("entity_id", flat=True)
        return qs.filter(
            Q(entity_id__in=entity_ids)
            | Q(participants=self.request.user)
            | Q(is_global=True)
        ).distinct()

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

    @action(detail=False, methods=["post"], permission_classes=[IsInternalUser])
    def broadcast(self, request, *args, **kwargs):
        serializer = GlobalMessageBroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        thread = MessageThread.objects.create(
            subject=serializer.validated_data["subject"],
            created_by=request.user,
            is_internal_only=False,
            is_global=True,
        )
        if request.user:
            thread.participants.add(request.user)
        message = thread.add_message(
            sender=request.user,
            content=serializer.validated_data["body"],
            attachments=serializer.validated_data.get("attachments") or [],
        )
        AuditLogEntry.record(
            actor=request.user,
            action="thread.broadcast",
            metadata={"thread_id": thread.pk, "message_id": message.pk},
        )
        response = self.get_serializer(thread)
        return Response(response.data, status=status.HTTP_201_CREATED)


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
