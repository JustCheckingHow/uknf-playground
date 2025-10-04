from __future__ import annotations

from rest_framework.permissions import BasePermission

from .models import User


class IsInternalUser(BasePermission):
    message = "Dostęp wymaga uprawnień użytkownika wewnętrznego."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_internal)


class IsEntityMember(BasePermission):
    message = "Dostęp wymaga powiązania z podmiotem."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.memberships.exists()


class HasRole(BasePermission):
    def __init__(self, *roles: User.UserRole):
        self.roles = {role for role in roles}

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in self.roles)
