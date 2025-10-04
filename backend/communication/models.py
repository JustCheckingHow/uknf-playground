from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import RegulatedEntity


class Report(models.Model):
    class ReportStatus(models.TextChoices):
        DRAFT = "draft", "Robocze"
        SUBMITTED = "submitted", "Przekazane"
        PROCESSING = "processing", "W trakcie"
        VALIDATED = "validated", "Proces walidacji zakończony sukcesem"
        VALIDATION_ERRORS = "validation_errors", "Błędy z reguł walidacji"
        TECHNICAL_FAILURE = "technical_failure", "Błąd techniczny w procesie"
        TIMEOUT = "timeout", "Błąd – przekroczono czas"
        DISPUTED = "disputed", "Zakwestionowane przez UKNF"

    entity = models.ForeignKey(RegulatedEntity, on_delete=models.CASCADE, related_name="reports")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="submitted_reports")
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=128)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=32, choices=ReportStatus.choices, default=ReportStatus.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    validation_errors = models.TextField(blank=True)
    file_path = models.CharField(max_length=512, blank=True)
    comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_submitted(self, user):
        self.submitted_by = user
        self.status = self.ReportStatus.SUBMITTED
        self.submitted_at = timezone.now()
        self.save(update_fields=["submitted_by", "status", "submitted_at", "updated_at"])

    def set_status(self, status: str, *, message: str | None = None) -> None:
        self.status = status
        if status == self.ReportStatus.VALIDATED:
            self.validated_at = timezone.now()
        if message:
            self.comments = message
        self.save(update_fields=["status", "validated_at", "comments", "updated_at"])

    def __str__(self) -> str:  # pragma: no cover
        return f"Report({self.title})"


class ReportTimelineEntry(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="timeline")
    status = models.CharField(max_length=32, choices=Report.ReportStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["created_at"]


class Case(models.Model):
    class CaseStatus(models.TextChoices):
        OPEN = "open", "Otwarte"
        IN_PROGRESS = "in_progress", "W toku"
        RESPONDED = "responded", "Odpowiedziano"
        CLOSED = "closed", "Zamknięte"

    entity = models.ForeignKey(RegulatedEntity, on_delete=models.CASCADE, related_name="cases")
    reference_code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=32, choices=CaseStatus.choices, default=CaseStatus.OPEN)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="assigned_cases")
    due_date = models.DateField(null=True, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def close(self, actor, notes: str = "") -> None:
        self.status = self.CaseStatus.CLOSED
        self.closed_at = timezone.now()
        CaseTimelineEntry.objects.create(case=self, status=self.status, created_by=actor, notes=notes)
        self.save(update_fields=["status", "closed_at", "updated_at"])

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Case({self.reference_code})"


class CaseTimelineEntry(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="timeline")
    status = models.CharField(max_length=32, choices=Case.CaseStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["created_at"]


class MessageThread(models.Model):
    entity = models.ForeignKey(RegulatedEntity, on_delete=models.CASCADE, related_name="message_threads")
    subject = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_threads")
    is_internal_only = models.BooleanField(default=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="message_threads", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_message(self, *, sender, content: str, attachments: list[str] | None = None, is_internal_note: bool = False) -> "Message":
        message = Message.objects.create(
            thread=self,
            sender=sender,
            body=content,
            attachments=attachments or [],
            is_internal_note=is_internal_note,
        )
        self.updated_at = timezone.now()
        self.save(update_fields=["updated_at"])
        return message

    def __str__(self) -> str:  # pragma: no cover
        return f"Thread({self.subject})"


class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    is_internal_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    summary = models.CharField(max_length=512)
    content = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    requires_acknowledgement = models.BooleanField(default=False)
    target_roles = models.JSONField(default=list)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="published_announcements")

    def acknowledgement_rate(self) -> float:
        total_memberships = max(self.acknowledgements.count(), 1)
        acknowledged = self.acknowledgements.filter(acknowledged=True).count()
        return acknowledged / total_memberships

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class AnnouncementAcknowledgement(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="acknowledgements")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    acknowledged = models.BooleanField(default=True)
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("announcement", "user")


class LibraryDocument(models.Model):
    class DocumentCategory(models.TextChoices):
        REPORTING = "reporting", "Raportowanie"
        SUPERVISION = "supervision", "Nadzór"
        LEGAL = "legal", "Prawo"
        FAQ = "faq", "FAQ"

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=64, choices=DocumentCategory.choices)
    version = models.CharField(max_length=32)
    published_at = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    document_url = models.URLField()
    is_mandatory = models.BooleanField(default=False)

    def __str__(self) -> str:  # pragma: no cover
        return f"LibraryDocument({self.title})"


class FaqEntry(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=128, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "question"]

    def __str__(self) -> str:  # pragma: no cover
        return self.question
