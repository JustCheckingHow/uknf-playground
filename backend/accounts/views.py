from __future__ import annotations

from typing import Any

from django.contrib.auth import login, logout
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied, NotFound

from administration.models import AuditLogEntry
from .models import (
    AccessRequest,
    AccessRequestAttachment,
    AccessRequestHistoryEntry,
    AccessRequestLine,
    AccessRequestLinePermission,
    AccessRequestMessage,
    AccessRequestMessageAttachment,
    ContactSubmission,
    EntityMembership,
    NotificationPreference,
    RegulatedEntity,
    User,
    UserSessionContext,
)
from .permissions import IsEntityMember, IsInternalUser
from .serializers import (
    ActivateAccountSerializer,
    AccessRequestAttachmentSerializer,
    AccessRequestAttachmentUploadSerializer,
    AccessRequestDecisionSerializer,
    AccessRequestMessageCreateSerializer,
    AccessRequestMessageSerializer,
    AccessRequestSerializer,
    AccessRequestUpdateSerializer,
    AuthTokenSerializer,
    ContactSubmissionSerializer,
    EntityMembershipSerializer,
    NotificationPreferenceSerializer,
    RegisterUserSerializer,
    RegulatedEntitySerializer,
    RoleDisplaySerializer,
    UserSerializer,
    UserSessionContextSerializer,
)
from .services import (
    approve_line,
    block_line,
    ensure_initial_access_request,
    return_to_requester,
    submit_access_request,
)

ROLE_DESCRIPTIONS = {
    User.UserRole.SYSTEM_ADMIN: "Pełna administracja systemem, konfiguracja i zarządzanie incydentami.",
    User.UserRole.SUPERVISOR: "Zarządzanie sprawami, zatwierdzanie sprawozdań i kontakt z podmiotami.",
    User.UserRole.ANALYST: "Analiza sprawozdań i materiałów raportowych.",
    User.UserRole.COMMUNICATION_OFFICER: "Publikowanie komunikatów i ogłoszeń dla podmiotów.",
    User.UserRole.AUDITOR: "Dostęp tylko do odczytu dla celów audytowych.",
    User.UserRole.ENTITY_ADMIN: "Zarządzanie użytkownikami w podmiocie i konfiguracja profilu.",
    User.UserRole.SUBMITTER: "Przesyłanie sprawozdań i dokumentów.",
    User.UserRole.REPRESENTATIVE: "Oficjalna korespondencja z UKNF.",
    User.UserRole.READ_ONLY: "Podgląd przesłanych materiałów i odpowiedzi.",
}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        AuditLogEntry.record(action="account.registration_submitted", metadata={"email": user.email})
        return Response(
            {
                "detail": "Link aktywacyjny został wysłany na podany adres e-mail.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        AuditLogEntry.record(actor=user, action="auth.login", metadata={"user_id": user.pk})
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        AuditLogEntry.record(actor=request.user, action="auth.logout")
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data: dict[str, Any] = {
            "user": UserSerializer(request.user).data,
            "memberships": EntityMembershipSerializer(request.user.memberships.select_related("entity"), many=True).data,
            "session": UserSessionContextSerializer(get_or_create_session(request.user)).data,
        }
        return Response(data)


def get_or_create_session(user: User) -> UserSessionContext:
    session, _ = UserSessionContext.objects.get_or_create(user=user, defaults={"acting_entity": None})
    return session


class RegulatedEntityViewSet(viewsets.ModelViewSet):
    queryset = RegulatedEntity.objects.all().order_by("name")
    serializer_class = RegulatedEntitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["sector", "status", "city"]
    search_fields = ["name", "registration_number"]
    ordering_fields = ["name", "registration_number", "updated_at"]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsInternalUser()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], permission_classes=[IsInternalUser])
    def verify(self, request, *args, **kwargs):
        entity = self.get_object()
        entity.last_verified_at = timezone.now()
        entity.save(update_fields=["last_verified_at"])
        AuditLogEntry.record(actor=request.user, action="entity.verified", metadata={"entity_id": entity.pk})
        return Response(self.get_serializer(entity).data)


class EntityMembershipViewSet(viewsets.ModelViewSet):
    queryset = EntityMembership.objects.select_related("user", "entity").all()
    serializer_class = EntityMembershipSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["entity"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_internal:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        actor: User = self.request.user
        entity = serializer.validated_data["entity"]
        self._assert_can_manage_entity(actor, entity)
        membership = serializer.save()
        AuditLogEntry.record(
            actor=actor,
            action="entity_membership.created",
            metadata={"membership_id": membership.pk, "entity_id": entity.pk},
        )

    def perform_update(self, serializer):
        actor: User = self.request.user
        membership: EntityMembership = serializer.instance
        self._assert_can_manage_entity(actor, membership.entity)
        serializer.save()
        AuditLogEntry.record(
            actor=actor,
            action="entity_membership.updated",
            metadata={"membership_id": membership.pk},
        )

    def perform_destroy(self, instance):
        actor: User = self.request.user
        self._assert_can_manage_entity(actor, instance.entity)
        metadata = {"membership_id": instance.pk, "entity_id": instance.entity_id}
        super().perform_destroy(instance)
        AuditLogEntry.record(actor=actor, action="entity_membership.deleted", metadata=metadata)

    def _assert_can_manage_entity(self, actor: User, entity: RegulatedEntity) -> None:
        if actor.is_internal:
            return
        if actor.role != User.UserRole.ENTITY_ADMIN:
            raise PermissionDenied("Brak uprawnień do zarządzania użytkownikami podmiotu.")
        if not entity.memberships.filter(user=actor, role=EntityMembership.MembershipRole.ADMIN).exists():
            raise PermissionDenied("Brak powiązania z podmiotem.")


class AccessRequestViewSet(viewsets.ModelViewSet):
    serializer_class = AccessRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        base = (
            AccessRequest.objects.select_related("requester", "decided_by")
            .prefetch_related(
                "lines__entity",
                "lines__permissions",
                "attachments",
                "history",
                "messages__attachments",
                "messages__sender",
            )
            .order_by("-created_at")
        )

        user = self.request.user
        if not user or not user.is_authenticated:
            return AccessRequest.objects.none()

        if user.is_internal:
            filter_name = (self.request.query_params.get("filter") or "").lower().strip()
            if filter_name == "moje-podmioty":
                base = base.filter(lines__entity__in=user.managed_entities.all())
            elif filter_name in {"wymaga-dzialania-uknf", "wymaga działania uknf"}:
                base = base.filter(next_actor=AccessRequest.NextActor.UKNF)
            elif filter_name == "obslugiwany-przez-uknf":
                base = base.filter(handled_by_uknf=True)
            return base.distinct()

        if user.role == User.UserRole.ENTITY_ADMIN:
            return (
                base.filter(
                    lines__entity__memberships__user=user,
                    lines__entity__memberships__role=EntityMembership.MembershipRole.ADMIN,
                )
                .distinct()
            )

        entity_ids = list(user.memberships.values_list("entity_id", flat=True))
        if entity_ids:
            return base.filter(lines__entity_id__in=entity_ids).distinct()

        return base.filter(requester=user).distinct()

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return AccessRequestUpdateSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):  # pragma: no cover - safety net
        raise MethodNotAllowed("POST")

    def perform_update(self, serializer):
        actor: User = self.request.user
        instance: AccessRequest = self.get_object()
        previous_status = instance.status
        data_fields = list(serializer.validated_data.keys())
        serializer.save()
        instance.sync_requester_snapshot()
        if not actor.is_internal:
            instance.mark_updated(actor=actor)
        instance.refresh_next_actor()
        AccessRequestHistoryEntry.objects.create(
            request=instance,
            actor=actor,
            action="request.updated",
            from_status=previous_status,
            to_status=instance.status,
            payload={"fields": data_fields},
        )
        AuditLogEntry.record(
            actor=actor,
            action="access_request.updated",
            metadata={"request_id": instance.pk, "fields": data_fields},
        )

    @action(detail=False, methods=["get"], url_path="my-active")
    def my_active(self, request, *args, **kwargs):
        access_request = (
            AccessRequest.objects.select_related("requester")
            .prefetch_related("lines")
            .filter(requester=request.user)
            .order_by("-created_at")
            .first()
        )
        if not access_request:
            access_request = ensure_initial_access_request(request.user)
        serializer = AccessRequestSerializer(access_request, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, *args, **kwargs):
        access_request = self.get_object()
        self._assert_can_edit(access_request, request.user)
        submit_access_request(access_request, request.user)
        AuditLogEntry.record(
            actor=request.user,
            action="access_request.submitted",
            metadata={"request_id": access_request.pk},
        )
        serializer = AccessRequestSerializer(access_request, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalUser], url_path="return")
    def request_changes(self, request, *args, **kwargs):
        access_request = self.get_object()
        reason = request.data.get("reason", "")
        return_to_requester(access_request, request.user, reason=reason)
        AuditLogEntry.record(
            actor=request.user,
            action="access_request.returned",
            metadata={"request_id": access_request.pk, "reason": reason},
        )
        serializer = AccessRequestSerializer(access_request, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="lines/(?P<line_id>[^/.]+)/approve")
    def approve_line(self, request, line_id=None, *args, **kwargs):
        access_request = self.get_object()
        line = self._get_line(access_request, line_id)
        self._assert_can_decide_line(line, request.user)
        notes = request.data.get("notes", "")
        approve_line(line, request.user, notes=notes)
        AuditLogEntry.record(
            actor=request.user,
            action="access_request.line_approved",
            metadata={"request_id": access_request.pk, "line_id": line.pk},
        )
        serializer = AccessRequestSerializer(access_request, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="lines/(?P<line_id>[^/.]+)/block")
    def block_line(self, request, line_id=None, *args, **kwargs):
        access_request = self.get_object()
        line = self._get_line(access_request, line_id)
        self._assert_can_decide_line(line, request.user)
        notes = request.data.get("notes", "")
        block_line(line, request.user, notes=notes)
        AuditLogEntry.record(
            actor=request.user,
            action="access_request.line_blocked",
            metadata={"request_id": access_request.pk, "line_id": line.pk},
        )
        serializer = AccessRequestSerializer(access_request, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, *args, **kwargs):
        access_request = self.get_object()
        if request.method.lower() == "get":
            serializer = AccessRequestMessageSerializer(
                access_request.messages.all(), many=True, context=self.get_serializer_context()
            )
            return Response(serializer.data)

        data_serializer = AccessRequestMessageCreateSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        is_internal = data_serializer.validated_data.get("is_internal", False)
        if is_internal and not request.user.is_internal:
            raise PermissionDenied("Tylko użytkownicy UKNF mogą publikować wewnętrzne wiadomości.")
        message = AccessRequestMessage.objects.create(
            request=access_request,
            sender=request.user,
            body=data_serializer.validated_data["body"],
            is_internal=is_internal,
        )
        for file_obj in request.FILES.getlist("attachments"):
            AccessRequestMessageAttachment.objects.create(
                message=message,
                file=file_obj,
                uploaded_by=request.user,
            )
        AccessRequestHistoryEntry.objects.create(
            request=access_request,
            actor=request.user,
            action="message.posted",
            payload={"message_id": message.pk, "is_internal": is_internal},
        )
        AuditLogEntry.record(
            actor=request.user,
            action="access_request.message_posted",
            metadata={"request_id": access_request.pk, "message_id": message.pk},
        )
        serializer = AccessRequestMessageSerializer(message, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="attachments")
    def upload_attachment(self, request, *args, **kwargs):
        access_request = self.get_object()
        self._assert_can_edit(access_request, request.user)
        serializer = AccessRequestAttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = AccessRequestAttachment.objects.create(
            request=access_request,
            uploaded_by=request.user,
            file=serializer.validated_data["file"],
            description=serializer.validated_data.get("description", ""),
        )
        if not request.user.is_internal:
            access_request.mark_updated(actor=request.user)
        AccessRequestHistoryEntry.objects.create(
            request=access_request,
            actor=request.user,
            action="attachment.added",
            payload={"attachment_id": attachment.pk},
        )
        AuditLogEntry.record(
            actor=request.user,
            action="access_request.attachment_added",
            metadata={"request_id": access_request.pk, "attachment_id": attachment.pk},
        )
        response_serializer = AccessRequestAttachmentSerializer(attachment, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _get_line(self, access_request: AccessRequest, line_id: str | None) -> AccessRequestLine:
        if not line_id:
            raise NotFound("Nie przekazano identyfikatora linii wniosku.")
        try:
            return access_request.lines.get(pk=line_id)
        except AccessRequestLine.DoesNotExist as exc:  # pragma: no cover - defensive
            raise NotFound("Linia wniosku nie istnieje.") from exc

    def _assert_can_edit(self, access_request: AccessRequest, actor: User) -> None:
        if actor.is_internal or access_request.requester_id == actor.id:
            return
        if actor.role == User.UserRole.ENTITY_ADMIN and access_request.lines.filter(
            entity__memberships__user=actor,
            entity__memberships__role=EntityMembership.MembershipRole.ADMIN,
        ).exists():
            return
        raise PermissionDenied("Brak uprawnień do modyfikacji wniosku.")

    def _assert_can_decide_line(self, line: AccessRequestLine, actor: User) -> None:
        if actor.is_internal:
            return
        if line.permissions.filter(code=AccessRequestLinePermission.PermissionCode.ENTITY_ADMIN).exists():
            raise PermissionDenied("Akceptacja tej linii wymaga użytkownika UKNF.")
        if actor.role != User.UserRole.ENTITY_ADMIN:
            raise PermissionDenied("Brak uprawnień do zarządzania linią wniosku.")
        if not line.entity.memberships.filter(user=actor, role=EntityMembership.MembershipRole.ADMIN).exists():
            raise PermissionDenied("Brak powiązania z podmiotem.")


class ContactSubmissionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = ContactSubmission.objects.select_related("entity", "handled_by")
    serializer_class = ContactSubmissionSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsInternalUser()]


class SessionContextView(APIView):
    permission_classes = [IsAuthenticated, IsEntityMember]

    def post(self, request, *args, **kwargs):
        session = get_or_create_session(request.user)
        serializer = UserSessionContextSerializer(instance=session, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditLogEntry.record(
            actor=request.user,
            action="session.set_entity",
            metadata={"entity_id": session.acting_entity_id},
        )
        return Response(UserSessionContextSerializer(session).data)


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ActivateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        AuditLogEntry.record(actor=user, action="account.activated", metadata={"user_id": user.pk})
        return Response({"detail": "Konto zostało aktywowane."})


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        preferences, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return Response(NotificationPreferenceSerializer(preferences).data)

    def put(self, request, *args, **kwargs):
        preferences, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(instance=preferences, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditLogEntry.record(actor=request.user, action="notifications.update", metadata=serializer.data)
        return Response(serializer.data)


class RoleCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = [
            RoleDisplaySerializer(
                {
                    "value": role.value,
                    "label": role.label,
                    "description": ROLE_DESCRIPTIONS.get(role, role.label),
                }
            ).data
            for role in User.UserRole
        ]
        return Response(data)


class UserDirectoryView(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("email")
    serializer_class = UserSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
