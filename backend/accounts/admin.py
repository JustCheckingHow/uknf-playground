from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AccessRequest,
    AccessRequestAttachment,
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


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Informacje dodatkowe",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "pesel",
                    "department",
                    "position_title",
                    "preferred_language",
                    "must_change_password",
                    "managed_entities",
                )
            },
        ),
    )
    list_display = ("email", "role", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    filter_horizontal = ("managed_entities",)


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
    list_display = ("reference_code", "requester", "status", "next_actor", "submitted_at", "decided_at")
    list_filter = ("status", "next_actor", "handled_by_uknf")
    search_fields = ("reference_code", "requester__email")


@admin.register(AccessRequestLine)
class AccessRequestLineAdmin(admin.ModelAdmin):
    list_display = ("request", "entity", "status", "next_actor", "decided_at")
    list_filter = ("status", "next_actor")
    search_fields = ("request__reference_code", "entity__name")


@admin.register(AccessRequestAttachment)
class AccessRequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ("request", "file", "uploaded_by", "created_at")
    search_fields = ("request__reference_code",)


@admin.register(AccessRequestMessage)
class AccessRequestMessageAdmin(admin.ModelAdmin):
    list_display = ("request", "sender", "is_internal", "created_at")
    list_filter = ("is_internal",)


@admin.register(AccessRequestMessageAttachment)
class AccessRequestMessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ("message", "file", "uploaded_by", "created_at")


@admin.register(AccessRequestLinePermission)
class AccessRequestLinePermissionAdmin(admin.ModelAdmin):
    list_display = ("line", "code", "status", "decided_at")
    list_filter = ("code", "status")


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender_email", "created_at", "handled_by")


@admin.register(UserSessionContext)
class UserSessionContextAdmin(admin.ModelAdmin):
    list_display = ("user", "acting_entity", "updated_at")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "notify_via_email", "notify_via_sms")
