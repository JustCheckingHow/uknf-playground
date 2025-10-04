from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AccessRequest,
    ContactSubmission,
    EntityMembership,
    NotificationPreference,
    RegulatedEntity,
    User,
    UserSessionContext,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Informacje dodatkowe", {"fields": ("role", "phone_number", "department", "position_title", "preferred_language", "must_change_password")}),
    )
    list_display = ("email", "role", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")


@admin.register(RegulatedEntity)
class RegulatedEntityAdmin(admin.ModelAdmin):
    list_display = ("name", "registration_number", "sector", "status")
    search_fields = ("name", "registration_number", "sector")


@admin.register(EntityMembership)
class EntityMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "entity", "role", "is_primary")
    list_filter = ("role", "is_primary")


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("entity_name", "requester_email", "status", "submitted_at")
    list_filter = ("status",)


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender_email", "created_at", "handled_by")


@admin.register(UserSessionContext)
class UserSessionContextAdmin(admin.ModelAdmin):
    list_display = ("user", "acting_entity", "updated_at")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "notify_via_email", "notify_via_sms")
