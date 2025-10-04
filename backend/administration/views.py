from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsInternalUser
from .models import AuditLogEntry, DataRetentionPolicy, MaintenanceWindow, PasswordPolicy
from .serializers import (
    AuditLogSerializer,
    DataRetentionPolicySerializer,
    MaintenanceWindowSerializer,
    PasswordPolicySerializer,
)


class PasswordPolicyView(APIView):
    permission_classes = [IsAuthenticated, IsInternalUser]

    def get(self, request, *args, **kwargs):
        policy, _ = PasswordPolicy.objects.get_or_create(id=1)
        return Response(PasswordPolicySerializer(policy).data)

    def put(self, request, *args, **kwargs):
        policy, _ = PasswordPolicy.objects.get_or_create(id=1)
        serializer = PasswordPolicySerializer(instance=policy, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditLogEntry.record(actor=request.user, action="password_policy.updated", metadata=serializer.data)
        return Response(serializer.data)


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AuditLogEntry.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsInternalUser]
    filterset_fields = ["severity", "actor"]
    ordering = ["-created_at"]


class DataRetentionPolicyViewSet(viewsets.ModelViewSet):
    queryset = DataRetentionPolicy.objects.all()
    serializer_class = DataRetentionPolicySerializer
    permission_classes = [IsAuthenticated, IsInternalUser]
    lookup_field = "data_type"


class MaintenanceWindowViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceWindow.objects.select_related("created_by")
    serializer_class = MaintenanceWindowSerializer
    permission_classes = [IsAuthenticated, IsInternalUser]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        AuditLogEntry.record(actor=self.request.user, action="maintenance_window.created", metadata={"id": instance.pk})

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLogEntry.record(actor=self.request.user, action="maintenance_window.updated", metadata={"id": instance.pk})

    def perform_destroy(self, instance):
        AuditLogEntry.record(actor=self.request.user, action="maintenance_window.deleted", metadata={"id": instance.pk})
        instance.delete()
