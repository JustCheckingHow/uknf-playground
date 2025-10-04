from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    DataRetentionPolicyViewSet,
    MaintenanceWindowViewSet,
    PasswordPolicyView,
)

router = DefaultRouter()
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
router.register(r"retention", DataRetentionPolicyViewSet, basename="retention")
router.register(r"maintenance", MaintenanceWindowViewSet, basename="maintenance")

urlpatterns = [
    path("password-policy", PasswordPolicyView.as_view(), name="password-policy"),
    path("", include(router.urls)),
]
