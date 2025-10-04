from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Adres e-mail musi być podany.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=extra_fields.get("username") or email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.UserRole.SYSTEM_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser musi mieć is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser musi mieć is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=False, blank=True)
    email = models.EmailField("adres e-mail", unique=True)

    class UserRole(models.TextChoices):
        SYSTEM_ADMIN = "system_admin", "Administrator systemu"
        SUPERVISOR = "supervisor", "Nadzorca"
        ANALYST = "analyst", "Analityk"
        COMMUNICATION_OFFICER = "communication_officer", "Koordynator komunikacji"
        AUDITOR = "auditor", "Audytor"
        ENTITY_ADMIN = "entity_admin", "Administrator podmiotu"
        SUBMITTER = "submitter", "Osoba raportująca"
        REPRESENTATIVE = "representative", "Przedstawiciel"
        READ_ONLY = "read_only", "Tylko podgląd"

    role = models.CharField(max_length=64, choices=UserRole.choices, default=UserRole.ENTITY_ADMIN)
    phone_number = models.CharField(max_length=32, blank=True, validators=[RegexValidator(r"^[0-9+ ]*$", "Niepoprawny numer telefonu")])
    department = models.CharField(max_length=128, blank=True)
    position_title = models.CharField(max_length=128, blank=True)
    preferred_language = models.CharField(max_length=16, default="pl")
    must_change_password = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    @property
    def is_internal(self) -> bool:
        return self.role in {
            self.UserRole.SYSTEM_ADMIN,
            self.UserRole.SUPERVISOR,
            self.UserRole.ANALYST,
            self.UserRole.COMMUNICATION_OFFICER,
            self.UserRole.AUDITOR,
        }

    def __str__(self) -> str:  # pragma: no cover - human-readable
        return f"{self.email} ({self.get_role_display()})"


class RegulatedEntity(models.Model):
    class EntityStatus(models.TextChoices):
        ACTIVE = "active", "Aktywny"
        SUSPENDED = "suspended", "Zawieszony"
        DECOMMISSIONED = "decommissioned", "Wycofany"

    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=64, unique=True)
    sector = models.CharField(max_length=64)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=16)
    city = models.CharField(max_length=128)
    country = models.CharField(max_length=64, default="PL")
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=32)
    website = models.URLField(blank=True)
    status = models.CharField(max_length=32, choices=EntityStatus.choices, default=EntityStatus.ACTIVE)
    data_source = models.CharField(max_length=128, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.registration_number})"


class EntityMembership(models.Model):
    class MembershipRole(models.TextChoices):
        ADMIN = "admin", "Administrator"
        SUBMITTER = "submitter", "Osoba raportująca"
        REPRESENTATIVE = "representative", "Przedstawiciel"
        VIEWER = "viewer", "Odczyt"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    entity = models.ForeignKey(RegulatedEntity, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=32, choices=MembershipRole.choices)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "entity", "role")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user.email} -> {self.entity.name} ({self.get_role_display()})"


class AccessRequest(models.Model):
    class AccessStatus(models.TextChoices):
        SUBMITTED = "submitted", "Złożony"
        UNDER_REVIEW = "under_review", "W trakcie analizy"
        APPROVED = "approved", "Zatwierdzony"
        REJECTED = "rejected", "Odrzucony"

    entity_name = models.CharField(max_length=255)
    entity_registration_number = models.CharField(max_length=64, blank=True)
    requester_name = models.CharField(max_length=255)
    requester_email = models.EmailField()
    requester_phone = models.CharField(max_length=32, blank=True)
    requested_role = models.CharField(max_length=64)
    justification = models.TextField()
    status = models.CharField(max_length=32, choices=AccessStatus.choices, default=AccessStatus.SUBMITTED)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="processed_access_requests")
    decision_notes = models.TextField(blank=True)

    def mark_reviewed(self, reviewer: User, status: str, notes: str = "") -> None:
        self.reviewed_by = reviewer
        self.status = status
        self.decision_notes = notes
        self.reviewed_at = timezone.now()
        self.save(update_fields=["reviewed_by", "status", "decision_notes", "reviewed_at"])

    def __str__(self) -> str:  # pragma: no cover
        return f"AccessRequest({self.entity_name}, {self.requester_email})"


class ContactSubmission(models.Model):
    sender_name = models.CharField(max_length=255)
    sender_email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    entity = models.ForeignKey(RegulatedEntity, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="handled_contact_messages")
    handled_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    def mark_handled(self, handler: User, notes: str = "") -> None:
        self.handled_by = handler
        self.handled_at = timezone.now()
        self.resolution_notes = notes
        self.save(update_fields=["handled_by", "handled_at", "resolution_notes"])

    def __str__(self) -> str:  # pragma: no cover
        return f"ContactSubmission({self.subject})"


class UserSessionContext(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_context")
    acting_entity = models.ForeignKey(RegulatedEntity, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Context({self.user.email} -> {self.acting_entity})"


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences")
    notify_via_email = models.BooleanField(default=True)
    notify_via_sms = models.BooleanField(default=False)
    daily_digest = models.BooleanField(default=True)
    weekly_digest = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Preferences({self.user.email})"
