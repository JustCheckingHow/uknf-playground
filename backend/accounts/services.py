from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import (
    AccessRequest,
    AccessRequestHistoryEntry,
    AccessRequestLine,
    AccessRequestLinePermission,
    EntityMembership,
    User,
)

logger = logging.getLogger(__name__)


# --- Konto użytkownika ----------------------------------------------------

def build_activation_link(user, request=None) -> tuple[str, str, str]:
    """Return activation link together with uid/token payload."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    configured_url = getattr(settings, "ACCOUNT_ACTIVATION_URL", "").strip()

    if configured_url:
        base = configured_url.rstrip("/")
        link = f"{base}?uid={uid}&token={token}"
    elif request is not None:
        api_path = reverse("activate")
        link = f"{request.build_absolute_uri(api_path)}?uid={uid}&token={token}"
    else:
        link = f"/activate?uid={uid}&token={token}"

    return link, uid, token


def send_activation_email(user, request=None) -> str:
    link, _, _ = build_activation_link(user, request=request)
    subject = "Aktywacja konta w Platformie Komunikacyjnej UKNF"
    message = (
        "Dzień dobry,\n\n"
        "Otrzymaliśmy wniosek o utworzenie konta w Platformie Komunikacyjnej UKNF.\n"
        "Aby dokończyć rejestrację i ustawić hasło, przejdź do poniższego odnośnika:\n\n"
        f"{link}\n\n"
        "Jeżeli nie inicjowałeś/aś tej rejestracji, zignoruj tę wiadomość."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    return link


# --- Wnioski o dostęp ------------------------------------------------------


@transaction.atomic
def ensure_initial_access_request(user: User) -> AccessRequest:
    request = AccessRequest.objects.filter(requester=user).order_by("-created_at").first()
    if request:
        request.sync_requester_snapshot()
        return request

    request = AccessRequest.objects.create(
        requester=user,
        requester_first_name=user.first_name,
        requester_last_name=user.last_name,
        requester_email=user.email,
        requester_phone=user.phone_number,
        requester_pesel=user.pesel,
    )
    AccessRequestHistoryEntry.objects.create(
        request=request,
        actor=user,
        action="request.created",
        to_status=AccessRequest.AccessStatus.DRAFT,
        payload={"auto": True},
    )
    return request


def _add_history_entry(
    request: AccessRequest,
    *,
    actor: User | None,
    action: str,
    from_status: str | None = None,
    to_status: str | None = None,
    payload: dict | None = None,
) -> None:
    AccessRequestHistoryEntry.objects.create(
        request=request,
        actor=actor,
        action=action,
        from_status=from_status or "",
        to_status=to_status or "",
        payload=payload or {},
    )


@transaction.atomic
def submit_access_request(access_request: AccessRequest, actor: User | None) -> AccessRequest:
    previous_status = access_request.status
    access_request.mark_submitted(actor=actor)
    _add_history_entry(
        access_request,
        actor=actor,
        action="request.submitted",
        from_status=previous_status,
        to_status=access_request.status,
    )
    _send_request_email(
        access_request,
        subject="Potwierdzenie złożenia wniosku o dostęp",
        body=(
            "Dzień dobry,\n\n"
            "Potwierdzamy złożenie wniosku o dostęp do platformy UKNF."
            " Status wniosku został zmieniony na 'Nowy'."
        ),
    )
    return access_request


@transaction.atomic
def approve_line(line: AccessRequestLine, actor: User, *, notes: str = "") -> AccessRequestLine:
    line.mark_approved(actor=actor, notes=notes)
    for permission in line.permissions.all():
        permission.mark_granted(actor=actor, notes=notes)
        _ensure_membership(permission.code, line.request.requester, line.entity)
    _add_history_entry(
        line.request,
        actor=actor,
        action="line.approved",
        payload={
            "entity_id": line.entity_id,
            "permissions": [perm.code for perm in line.permissions.all()],
        },
    )
    _refresh_request_status(line.request, actor=actor, notes=notes)
    return line


@transaction.atomic
def block_line(line: AccessRequestLine, actor: User, *, notes: str = "") -> AccessRequestLine:
    line.mark_blocked(actor=actor, notes=notes)
    for permission in line.permissions.all():
        permission.mark_blocked(actor=actor, notes=notes)
        if permission.code == AccessRequestLinePermission.PermissionCode.ENTITY_ADMIN:
            _deactivate_administrator(line.request.requester)
    _add_history_entry(
        line.request,
        actor=actor,
        action="line.blocked",
        payload={
            "entity_id": line.entity_id,
            "permissions": [perm.code for perm in line.permissions.all()],
            "notes": notes,
        },
    )
    _refresh_request_status(line.request, actor=actor, notes=notes)
    return line


@transaction.atomic
def return_to_requester(access_request: AccessRequest, actor: User, *, reason: str = "") -> AccessRequest:
    previous_status = access_request.status
    access_request.status = AccessRequest.AccessStatus.UPDATED
    access_request.next_actor = AccessRequest.NextActor.REQUESTER
    access_request.decision_notes = reason
    update_fields = ["status", "next_actor", "decision_notes", "updated_at"]
    if actor.is_internal and not access_request.handled_by_uknf:
        access_request.handled_by_uknf = True
        update_fields.append("handled_by_uknf")
    access_request.save(update_fields=update_fields)
    _add_history_entry(
        access_request,
        actor=actor,
        action="request.returned",
        from_status=previous_status,
        to_status=access_request.status,
        payload={"reason": reason},
    )
    _send_request_email(
        access_request,
        subject="Wniosek o dostęp wymaga uzupełnienia",
        body=(
            "Dzień dobry,\n\n"
            "Pracownik UKNF poprosił o uzupełnienie danych we wniosku o dostęp."\
            " Zaloguj się do systemu i wprowadź wymagane zmiany."
        ),
    )
    return access_request


def _refresh_request_status(access_request: AccessRequest, *, actor: User | None = None, notes: str = "") -> None:
    total = access_request.lines.count()
    approved = access_request.lines.filter(status=AccessRequestLine.LineStatus.APPROVED).count()
    blocked = access_request.lines.filter(status=AccessRequestLine.LineStatus.BLOCKED).count()

    if total == 0:
        access_request.mark_updated(actor=actor)
        return

    pending = total - approved - blocked
    if pending > 0:
        access_request.refresh_next_actor()
        return

    if approved == total:
        access_request.mark_approved(actor=actor or access_request.requester, notes=notes)
        _add_history_entry(
            access_request,
            actor=actor,
            action="request.approved",
            to_status=AccessRequest.AccessStatus.APPROVED,
            payload={"notes": notes},
        )
        _send_request_email(
            access_request,
            subject="Wniosek o dostęp został zaakceptowany",
            body=(
                "Dzień dobry,\n\n"
                "Twój wniosek o dostęp został zaakceptowany. Możesz zalogować się do systemu"
                " i korzystać z przypisanych uprawnień."
            ),
        )
        return

    if blocked == total:
        access_request.mark_blocked(actor=actor or access_request.requester, notes=notes)
        _add_history_entry(
            access_request,
            actor=actor,
            action="request.blocked",
            to_status=AccessRequest.AccessStatus.BLOCKED,
            payload={"notes": notes},
        )
        _send_request_email(
            access_request,
            subject="Wniosek o dostęp został zablokowany",
            body=(
                "Dzień dobry,\n\n"
                "Twój wniosek o dostęp został zablokowany. Skontaktuj się z administratorem"
                " w celu uzyskania dodatkowych informacji."
            ),
        )
        return

    # Mieszany wynik – oznacz jako zaakceptowany częściowo
    access_request.mark_approved(actor=actor or access_request.requester, notes=notes)
    access_request.decision_notes = "Część uprawnień została zablokowana."
    access_request.save(update_fields=["decision_notes", "updated_at"])
    _add_history_entry(
        access_request,
        actor=actor,
        action="request.partial",
        to_status=access_request.status,
        payload={"approved": approved, "blocked": blocked, "notes": notes},
    )


def _ensure_membership(permission_code: str, user: User, entity) -> None:
    role_mapping = {
        AccessRequestLinePermission.PermissionCode.REPORTING: EntityMembership.MembershipRole.SUBMITTER,
        AccessRequestLinePermission.PermissionCode.CASES: EntityMembership.MembershipRole.REPRESENTATIVE,
        AccessRequestLinePermission.PermissionCode.ENTITY_ADMIN: EntityMembership.MembershipRole.ADMIN,
    }
    membership_role = role_mapping.get(permission_code)
    if not membership_role:
        return

    EntityMembership.objects.get_or_create(
        user=user,
        entity=entity,
        role=membership_role,
        defaults={"is_primary": membership_role == EntityMembership.MembershipRole.ADMIN},
    )


def _deactivate_administrator(user: User) -> None:
    if user.role != User.UserRole.ENTITY_ADMIN:
        return

    if not user.is_active:
        return

    user.is_active = False
    user.save(update_fields=["is_active"])


def _send_request_email(access_request: AccessRequest, *, subject: str, body: str) -> None:
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [access_request.requester_email])
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Nie udało się wysłać e-maila dotyczącego wniosku %s: %s", access_request.pk, exc)
