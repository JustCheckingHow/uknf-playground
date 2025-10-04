from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


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
    pesel = models.CharField(
        max_length=11,
        blank=True,
        validators=[RegexValidator(r"^\d{11}$", "Niepoprawny numer PESEL")],
        help_text="Numer PESEL użytkownika przechowywany na potrzeby weryfikacji.",
    )
    department = models.CharField(max_length=128, blank=True)
    position_title = models.CharField(max_length=128, blank=True)
    preferred_language = models.CharField(max_length=16, default="pl")
    must_change_password = models.BooleanField(default=False)
    managed_entities = models.ManyToManyField("accounts.RegulatedEntity", related_name="managed_by", blank=True)

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

    @property
    def pesel_masked(self) -> str:
        if not self.pesel:
            return ""
        visible = self.pesel[-4:]
        hidden = "*" * max(len(self.pesel) - 4, 0)
        return f"{hidden}{visible}"


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
        DRAFT = "draft", "Roboczy"
        NEW = "new", "Nowy"
        APPROVED = "approved", "Zaakceptowany"
        BLOCKED = "blocked", "Zablokowany"
        UPDATED = "updated", "Zaktualizowany"

    class NextActor(models.TextChoices):
        REQUESTER = "requester", "Wnioskodawca"
        ENTITY_ADMIN = "entity_admin", "Administrator podmiotu"
        UKNF = "uknf", "UKNF"
        NONE = "none", "Brak"

    reference_code = models.CharField(max_length=24, unique=True, editable=False)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access_requests")
    status = models.CharField(max_length=32, choices=AccessStatus.choices, default=AccessStatus.DRAFT)
    next_actor = models.CharField(max_length=32, choices=NextActor.choices, default=NextActor.REQUESTER)
    handled_by_uknf = models.BooleanField(default=False)

    requester_first_name = models.CharField(max_length=150)
    requester_last_name = models.CharField(max_length=150)
    requester_email = models.EmailField()
    requester_phone = models.CharField(max_length=32, blank=True)
    requester_pesel = models.CharField(max_length=11, blank=True)

    justification = models.TextField(blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_access_requests",
    )
    decision_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating and not self.reference_code:
            self.reference_code = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self) -> str:
        return f"AR-{get_random_string(10).upper()}"

    @property
    def requester_pesel_masked(self) -> str:
        if not self.requester_pesel:
            return ""
        visible = self.requester_pesel[-4:]
        hidden = "*" * max(len(self.requester_pesel) - 4, 0)
        return f"{hidden}{visible}"

    def mark_submitted(self, *, actor: User | None = None) -> None:
        self.status = self.AccessStatus.NEW
        self.submitted_at = timezone.now()
        self.next_actor = self._compute_next_actor()
        self.decision_notes = ""
        self.decided_by = None
        self.decided_at = None
        self.save(update_fields=["status", "submitted_at", "next_actor", "decision_notes", "decided_by", "decided_at", "updated_at"])

    def mark_updated(self, *, actor: User | None = None) -> None:
        target_status = self.AccessStatus.UPDATED if self.status == self.AccessStatus.APPROVED else self.AccessStatus.NEW
        self.status = target_status
        self.next_actor = self._compute_next_actor()
        self.save(update_fields=["status", "next_actor", "updated_at"])

    def mark_approved(self, *, actor: User, notes: str = "") -> None:
        self.status = self.AccessStatus.APPROVED
        self.decision_notes = notes
        self.decided_by = actor
        self.decided_at = timezone.now()
        self.next_actor = self.NextActor.NONE
        self.handled_by_uknf = self.handled_by_uknf or actor.is_internal
        self.save(
            update_fields=[
                "status",
                "decision_notes",
                "decided_by",
                "decided_at",
                "next_actor",
                "handled_by_uknf",
                "updated_at",
            ]
        )

    def mark_blocked(self, *, actor: User, notes: str = "") -> None:
        self.status = self.AccessStatus.BLOCKED
        self.decision_notes = notes
        self.decided_by = actor
        self.decided_at = timezone.now()
        self.next_actor = self.NextActor.NONE
        self.handled_by_uknf = self.handled_by_uknf or actor.is_internal
        self.save(
            update_fields=[
                "status",
                "decision_notes",
                "decided_by",
                "decided_at",
                "next_actor",
                "handled_by_uknf",
                "updated_at",
            ]
        )

    def _compute_next_actor(self) -> str:
        if self.status == self.AccessStatus.DRAFT:
            return self.NextActor.REQUESTER
        if self.status in {self.AccessStatus.APPROVED, self.AccessStatus.BLOCKED}:
            return self.NextActor.NONE
        if self.lines.filter(next_actor=AccessRequestLine.NextActor.UKNF).exists():
            return self.NextActor.UKNF
        if self.lines.filter(next_actor=AccessRequestLine.NextActor.ENTITY_ADMIN).exists():
            return self.NextActor.ENTITY_ADMIN
        return self.NextActor.NONE

    def refresh_next_actor(self) -> None:
        next_actor = self._compute_next_actor()
        if self.next_actor != next_actor:
            self.next_actor = next_actor
            self.save(update_fields=["next_actor", "updated_at"])

    def sync_requester_snapshot(self) -> None:
        self.requester_first_name = self.requester.first_name
        self.requester_last_name = self.requester.last_name
        self.requester_email = self.requester.email
        self.requester_phone = self.requester.phone_number
        self.requester_pesel = self.requester.pesel
        self.save(
            update_fields=[
                "requester_first_name",
                "requester_last_name",
                "requester_email",
                "requester_phone",
                "requester_pesel",
                "updated_at",
            ]
        )

    def __str__(self) -> str:  # pragma: no cover
        return f"AccessRequest({self.reference_code})"


class AccessRequestHistoryEntry(models.Model):
    request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)
    from_status = models.CharField(max_length=32, choices=AccessRequest.AccessStatus.choices, blank=True)
    to_status = models.CharField(max_length=32, choices=AccessRequest.AccessStatus.choices, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class AccessRequestAttachment(models.Model):
    request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to="access_requests/attachments/%Y/%m/%d")
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Attachment({self.file.name})"


class AccessRequestLine(models.Model):
    class LineStatus(models.TextChoices):
        PENDING = "pending", "Oczekujące"
        APPROVED = "approved", "Zaakceptowane"
        BLOCKED = "blocked", "Zablokowane"
        NEEDS_UPDATE = "needs_update", "Wymaga aktualizacji"

    class NextActor(models.TextChoices):
        REQUESTER = "requester", "Wnioskodawca"
        ENTITY_ADMIN = "entity_admin", "Administrator podmiotu"
        UKNF = "uknf", "UKNF"
        NONE = "none", "Brak"

    request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE, related_name="lines")
    entity = models.ForeignKey(RegulatedEntity, on_delete=models.CASCADE, related_name="access_request_lines")
    status = models.CharField(max_length=32, choices=LineStatus.choices, default=LineStatus.PENDING)
    next_actor = models.CharField(max_length=32, choices=NextActor.choices, default=NextActor.ENTITY_ADMIN)
    contact_email = models.EmailField(blank=True)
    decision_notes = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_access_request_lines",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("request", "entity")

    def set_next_actor_from_permissions(self) -> None:
        if self.status in {self.LineStatus.APPROVED, self.LineStatus.BLOCKED}:
            self.next_actor = self.NextActor.NONE
            return
        if self.permissions.filter(code=AccessRequestLinePermission.PermissionCode.ENTITY_ADMIN).exists():
            self.next_actor = self.NextActor.UKNF
            return
        self.next_actor = self.NextActor.ENTITY_ADMIN

    def save(self, *args, **kwargs):
        self.set_next_actor_from_permissions()
        super().save(*args, **kwargs)
        if self.contact_email:
            self.entity.contact_email = self.contact_email
            self.entity.save(update_fields=["contact_email", "updated_at"])

    def mark_approved(self, *, actor: User, notes: str = "") -> None:
        self.status = self.LineStatus.APPROVED
        self.decision_notes = notes
        self.decided_by = actor
        self.decided_at = timezone.now()
        self.next_actor = self.NextActor.NONE
        self.save(update_fields=["status", "decision_notes", "decided_by", "decided_at", "next_actor", "updated_at"])

    def mark_blocked(self, *, actor: User, notes: str = "") -> None:
        self.status = self.LineStatus.BLOCKED
        self.decision_notes = notes
        self.decided_by = actor
        self.decided_at = timezone.now()
        self.next_actor = self.NextActor.NONE
        self.save(update_fields=["status", "decision_notes", "decided_by", "decided_at", "next_actor", "updated_at"])

    def requires_uknf(self) -> bool:
        return self.permissions.filter(code=AccessRequestLinePermission.PermissionCode.ENTITY_ADMIN).exists()

    def __str__(self) -> str:  # pragma: no cover
        return f"AccessRequestLine({self.request.reference_code} -> {self.entity.name})"


class AccessRequestLinePermission(models.Model):
    class PermissionCode(models.TextChoices):
        REPORTING = "reporting", "Sprawozdawczość"
        CASES = "cases", "Sprawy"
        ENTITY_ADMIN = "entity_admin", "Administrator podmiotu"

    class PermissionStatus(models.TextChoices):
        REQUESTED = "requested", "Wnioskowane"
        GRANTED = "granted", "Przyznane"
        BLOCKED = "blocked", "Zablokowane"

    line = models.ForeignKey(AccessRequestLine, on_delete=models.CASCADE, related_name="permissions")
    code = models.CharField(max_length=32, choices=PermissionCode.choices)
    status = models.CharField(max_length=16, choices=PermissionStatus.choices, default=PermissionStatus.REQUESTED)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_access_request_permissions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("line", "code")

    def mark_granted(self, *, actor: User, notes: str = "") -> None:
        self.status = self.PermissionStatus.GRANTED
        self.decided_by = actor
        self.decided_at = timezone.now()
        self.notes = notes
        self.save(update_fields=["status", "decided_by", "decided_at", "notes"])

    def mark_blocked(self, *, actor: User, notes: str = "") -> None:
        self.status = self.PermissionStatus.BLOCKED
        self.decided_by = actor
        self.decided_at = timezone.now()
        self.notes = notes
        self.save(update_fields=["status", "decided_by", "decided_at", "notes"])


class AccessRequestMessage(models.Model):
    request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class AccessRequestMessageAttachment(models.Model):
    message = models.ForeignKey(AccessRequestMessage, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="access_requests/messages/%Y/%m/%d")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"MessageAttachment({self.file.name})"


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
