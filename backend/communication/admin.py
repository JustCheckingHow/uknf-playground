from __future__ import annotations

from django.contrib import admin

from .models import (
    Announcement,
    AnnouncementAcknowledgement,
    Case,
    CaseTimelineEntry,
    FaqEntry,
    LibraryDocument,
    Message,
    MessageThread,
    Report,
    ReportTimelineEntry,
)


class ReportTimelineInline(admin.TabularInline):
    model = ReportTimelineEntry
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "entity", "status", "submitted_at", "validated_at")
    list_filter = ("status", "report_type")
    search_fields = ("title", "entity__name", "report_type")
    inlines = [ReportTimelineInline]


class CaseTimelineInline(admin.TabularInline):
    model = CaseTimelineEntry
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "entity", "status", "assigned_to", "due_date")
    list_filter = ("status",)
    search_fields = ("reference_code", "title", "entity__name")
    inlines = [CaseTimelineInline]


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ("subject", "entity", "created_by", "is_internal_only", "updated_at")
    search_fields = ("subject", "entity__name")
    inlines = [MessageInline]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "requires_acknowledgement")
    list_filter = ("requires_acknowledgement",)


@admin.register(AnnouncementAcknowledgement)
class AnnouncementAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ("announcement", "user", "acknowledged_at")


@admin.register(LibraryDocument)
class LibraryDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "version", "published_at", "is_mandatory")
    list_filter = ("category", "is_mandatory")
    search_fields = ("title", "description")


@admin.register(FaqEntry)
class FaqEntryAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("question", "answer")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "sender", "created_at", "is_internal_note")
    list_filter = ("is_internal_note",)


@admin.register(ReportTimelineEntry)
class ReportTimelineEntryAdmin(admin.ModelAdmin):
    list_display = ("report", "status", "created_at", "created_by")


@admin.register(CaseTimelineEntry)
class CaseTimelineEntryAdmin(admin.ModelAdmin):
    list_display = ("case", "status", "created_at", "created_by")
