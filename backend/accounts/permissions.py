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
    roles: set[User.UserRole] = set()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.roles
        )

    @classmethod
    def for_roles(cls, *roles: User.UserRole):
        allowed_roles = set(roles)

        class RolePermission(cls):
            roles = allowed_roles

        return RolePermission
