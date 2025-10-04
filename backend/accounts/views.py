from __future__ import annotations

from typing import Any

from django.contrib.auth import login, logout
from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from administration.models import AuditLogEntry
from .models import (
    AccessRequest,
    ContactSubmission,
    EntityMembership,
    NotificationPreference,
    RegulatedEntity,
    User,
    UserSessionContext,
)
from .permissions import IsEntityMember, IsInternalUser
from .serializers import (
    AccessRequestDecisionSerializer,
    AccessRequestSerializer,
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
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        AuditLogEntry.record(actor=user, action="account.register", metadata={"email": user.email})
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


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

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsInternalUser()]
        return super().get_permissions()


class AccessRequestViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AccessRequest.objects.select_related("reviewed_by").order_by("-submitted_at")
    serializer_class = AccessRequestSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsInternalUser()]

    def perform_create(self, serializer):
        access_request = serializer.save()
        AuditLogEntry.record(action="access_request.submitted", metadata={"request_id": access_request.pk})

    @action(detail=True, methods=["post"], permission_classes=[IsInternalUser])
    def decision(self, request, *args, **kwargs):
        access_request = self.get_object()
        serializer = AccessRequestDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_request.mark_reviewed(
            reviewer=request.user,
            status=serializer.validated_data["status"],
            notes=serializer.validated_data.get("decision_notes", ""),
        )
        AuditLogEntry.record(
            actor=request.user,
            action="access_request.reviewed",
            metadata={"request_id": access_request.pk, "status": access_request.status},
        )
        return Response(AccessRequestSerializer(access_request).data)


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
