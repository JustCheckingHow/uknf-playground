from __future__ import annotations

import json
import logging
import shutil
from datetime import date, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import EntityMembership, RegulatedEntity
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
from .filters import MessageThreadFilter
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


class UploadPreparationError(Exception):
    """Raised when an uploaded report file cannot be prepared for validation."""


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related("entity", "submitted_by").prefetch_related("timeline")
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["entity", "status", "report_type"]
    ordering_fields = ["submitted_at", "validated_at", "created_at"]
    search_fields = ["title", "entity__name", "report_type"]

    def _resolve_entity_id(self, request) -> int | None:
        entity_id = request.data.get("entity_id") or request.query_params.get("entity_id")
        if entity_id is not None:
            try:
                entity_id = int(entity_id)
            except (TypeError, ValueError):
                return None
            if request.user.is_internal:
                return entity_id
            member_entities = set(
                EntityMembership.objects.filter(user=request.user).values_list("entity_id", flat=True)
            )
            return entity_id if entity_id in member_entities else None
        membership = (
            EntityMembership.objects.filter(user=request.user)
            .exclude(entity__isnull=True)
            .order_by("created_at")
            .values_list("entity_id", flat=True)
            .first()
        )
        return int(membership) if membership else None

    def _prepare_upload(self, uploaded_file):
        storage_key = f"reports/{uuid4().hex}_{uploaded_file.name}"
        storage_path = default_storage.save(storage_key, uploaded_file)

        def cleanup_storage() -> None:
            try:
                default_storage.delete(storage_path)
            except Exception:  # pragma: no cover - best effort cleanup
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
            raise UploadPreparationError("Nie udało się przygotować pliku do walidacji.")

        return storage_path, cleanup_storage, local_path, temp_copy

    def _get_or_create_entity(self, request, metadata: dict[str, object] | None) -> RegulatedEntity:
        entity_id = self._resolve_entity_id(request)
        if entity_id:
            return RegulatedEntity.objects.get(pk=entity_id)

        metadata = metadata or {}
        identifier = str(metadata.get("entity_identifier") or "").strip() or None
        entity_name = str(metadata.get("entity_name") or "").strip() or None

        if identifier:
            existing = RegulatedEntity.objects.filter(registration_number__iexact=identifier).first()
            if existing:
                return existing

        if entity_name:
            existing = RegulatedEntity.objects.filter(name__iexact=entity_name).first()
            if existing:
                if identifier and not existing.registration_number:
                    existing.registration_number = identifier
                    existing.save(update_fields=["registration_number", "updated_at"])
                return existing

        name = entity_name or f"Podmiot {request.user.email}" if request.user.email else f"Podmiot {uuid4().hex[:6]}"
        registration_number = identifier or f"UNASSIGNED-{uuid4().hex[:10]}"

        defaults = {
            "name": name[:255],
            "registration_number": registration_number,
            "sector": str(metadata.get("register") or "Nieznany")[:64],
            "address": str(metadata.get("entity_address") or "Nieznany")[:255],
            "postal_code": str(metadata.get("postal_code") or "00-000")[:16],
            "city": str(metadata.get("entity_city") or "Nieznane")[:128],
            "country": str(metadata.get("entity_country") or "PL")[:64],
            "contact_email": request.user.email or f"kontakt+{uuid4().hex[:6]}@example.com",
            "contact_phone": str(metadata.get("contact_phone") or "Brak" )[:32],
            "website": str(metadata.get("website") or "")[:200],
            "status": RegulatedEntity.EntityStatus.ACTIVE,
            "data_source": "upload_new",
            "notes": "Podmiot utworzony automatycznie podczas przesyłania sprawozdania.",
            "last_verified_at": timezone.now(),
        }

        entity, created = RegulatedEntity.objects.get_or_create(
            registration_number=registration_number,
            defaults=defaults,
        )
        if created and entity.name != name:
            entity.name = name[:255]
            entity.save(update_fields=["name", "updated_at"])

        if not request.user.is_internal:
            EntityMembership.objects.get_or_create(
                user=request.user,
                entity=entity,
                role=EntityMembership.MembershipRole.SUBMITTER,
                defaults={"is_primary": True},
            )

        return entity

    def _apply_upload_results(
        self,
        *,
        report: Report,
        uploaded_file,
        validation_result,
        validation_payload,
        storage_path: str,
        request,
    ) -> None:
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

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_internal:
            return qs
        entity_ids = EntityMembership.objects.filter(user=self.request.user).values_list("entity_id", flat=True)
        return qs.filter(Q(entity_id__in=entity_ids) | Q(submitted_by=self.request.user))

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
        try:
            storage_path, cleanup_storage, local_path, temp_copy = self._prepare_upload(uploaded_file)
        except UploadPreparationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        validation_payload: dict[str, object] | None = None
        try:
            validation_result = validate_report_workbook(local_path)
            validation_payload = validation_result.to_dict()
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
        if validation_payload is None:
            validation_payload = validation_result.to_dict()
        try:
            self._apply_upload_results(
                report=report,
                uploaded_file=uploaded_file,
                validation_result=validation_result,
                validation_payload=validation_payload,
                storage_path=storage_path,
                request=request,
            )
        except Exception:
            cleanup_storage()
            raise

        serializer = self.get_serializer(report)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser],
    )
    def upload_new(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Nie przesłano pliku."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            storage_path, cleanup_storage, local_path, temp_copy = self._prepare_upload(uploaded_file)
        except UploadPreparationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        validation_payload: dict[str, object] | None = None
        try:
            validation_result = validate_report_workbook(local_path)
            validation_payload = validation_result.to_dict()
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

        metadata = validation_payload.get("metadata", {}) if validation_payload else {}
        entity = self._get_or_create_entity(request, metadata)
        if not request.user.is_internal:
            member_entities = set(
                EntityMembership.objects.filter(user=request.user).values_list("entity_id", flat=True)
            )
            if member_entities and entity.pk not in member_entities:
                cleanup_storage()
                return Response(
                    {"detail": "Nie masz uprawnień do przesyłania sprawozdania dla tego podmiotu."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        period_start_raw = metadata.get("period_start") if isinstance(metadata, dict) else None
        period_end_raw = metadata.get("period_end") if isinstance(metadata, dict) else None

        try:
            period_start = date.fromisoformat(str(period_start_raw))
            period_end = date.fromisoformat(str(period_end_raw))
        except (TypeError, ValueError):
            cleanup_storage()
            return Response(
                {"detail": "Nie udało się odczytać zakresu okresu sprawozdawczego z pliku."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        title_source = metadata.get("form_name") if isinstance(metadata, dict) else None
        report_type_source = metadata.get("form_id") if isinstance(metadata, dict) else None
        title = (str(title_source).strip() if title_source else Path(uploaded_file.name).stem) or "Sprawozdanie"
        report_type = (str(report_type_source).strip() if report_type_source else metadata.get("register") if isinstance(metadata, dict) else None) or "Nieznany"

        title = title[:255]
        report_type = report_type[:128]

        try:
            with transaction.atomic():
                report = Report.objects.create(
                    entity=entity,
                    submitted_by=request.user,
                    title=title,
                    report_type=report_type,
                    period_start=period_start,
                    period_end=period_end,
                )
        except Exception:
            cleanup_storage()
            raise

        try:
            self._apply_upload_results(
                report=report,
                uploaded_file=uploaded_file,
                validation_result=validation_result,
                validation_payload=validation_payload,
                storage_path=storage_path,
                request=request,
            )
        except Exception:
            cleanup_storage()
            report.delete()  # best-effort rollback if processing fails
            raise

        if validation_payload is None:
            validation_payload = validation_result.to_dict()

        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
        MessageThread.objects.select_related("entity", "created_by", "target_group")
        .prefetch_related("participants", "messages", "messages__sender", "messages__recipient")
        .order_by("-updated_at")
    )
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = MessageThreadFilter

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_internal:
            return qs
        entity_ids = EntityMembership.objects.filter(user=self.request.user).values_list("entity_id", flat=True)
        return qs.filter(
            Q(entity_id__in=entity_ids)
            | Q(participants=self.request.user)
            | Q(is_global=True)
            | Q(target_group__users=self.request.user)
            | Q(target_user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        thread = serializer.save()
        AuditLogEntry.record(actor=self.request.user, action="thread.created", metadata={"thread_id": thread.pk})

    @action(
        detail=True,
        methods=["get", "post"],
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    def messages(self, request, *args, **kwargs):
        thread = self.get_object()
        if request.method == "GET":
            messages = thread.messages.select_related("sender", "recipient")
            if not request.user.is_internal:
                messages = messages.filter(
                    Q(recipient__isnull=True)
                    | Q(recipient=request.user)
                    | Q(sender=request.user)
                )
            serialized = MessageSerializer(messages, many=True, context={"request": request})
            return Response(serialized.data)
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.validated_data.get("attachment")
        recipient = None
        if request.user.is_internal:
            if thread.target_user:
                recipient = thread.target_user
        else:
            recipient = thread.created_by
            if recipient is None:
                recipient = thread.participants.filter(is_internal=True).first()
        message = thread.add_message(
            sender=request.user,
            content=serializer.validated_data["body"],
            is_internal_note=serializer.validated_data.get("is_internal_note", False),
            attachment=attachment,
            recipient=recipient,
        )
        AuditLogEntry.record(
            actor=request.user,
            action="thread.message",
            metadata={"thread_id": thread.pk, "message_id": message.pk},
        )
        serialized = MessageSerializer(message, context={"request": request})
        return Response(serialized.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsInternalUser],
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    def broadcast(self, request, *args, **kwargs):
        serializer = GlobalMessageBroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        thread = MessageThread.objects.create(
            subject=serializer.validated_data["subject"],
            created_by=request.user,
            is_internal_only=False,
            is_global=serializer.validated_data["target_type"] == "group",
            target_group=serializer.validated_data.get("group"),
            target_user=serializer.validated_data.get("user"),
        )
        thread.participants.add(request.user)
        if thread.target_user:
            thread.participants.add(thread.target_user)
        message = thread.add_message(
            sender=request.user,
            content=serializer.validated_data["body"],
            attachment=serializer.validated_data.get("attachment"),
            recipient=thread.target_user,
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
