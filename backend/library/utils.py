from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, QuerySet

from accounts.models import User
from communication.models import LibraryDocument

_INTERNAL_ROLES = {
    User.UserRole.SYSTEM_ADMIN,
    User.UserRole.SUPERVISOR,
    User.UserRole.ANALYST,
    User.UserRole.COMMUNICATION_OFFICER,
    User.UserRole.AUDITOR,
}


def _admin_uploaded_filter() -> Q:
    return Q(uploaded_by__role__in=_INTERNAL_ROLES) | Q(uploaded_by__isnull=True)


def filter_documents_for_user(
    queryset: QuerySet[LibraryDocument],
    user: Optional[User | AnonymousUser],
) -> QuerySet[LibraryDocument]:
    if user and getattr(user, "is_internal", False):
        return queryset
    return queryset.filter(_admin_uploaded_filter())


__all__ = ["filter_documents_for_user"]
