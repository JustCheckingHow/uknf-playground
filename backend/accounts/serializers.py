from __future__ import annotations

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    AccessRequest,
    AccessRequestAttachment,
    AccessRequestHistoryEntry,
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


class RoleDisplaySerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    pesel_masked = serializers.CharField(read_only=True)
    managed_entities = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
            "pesel_masked",
            "phone_number",
            "department",
            "position_title",
            "preferred_language",
            "is_active",
            "is_staff",
            "is_internal",
            "managed_entities",
        ]
        read_only_fields = ["is_staff", "is_internal", "is_active"]


class RegisterUserSerializer(serializers.ModelSerializer):
    pesel = serializers.CharField(write_only=True, max_length=11)

    ALLOWED_ROLES = {
        User.UserRole.ENTITY_ADMIN,
        User.UserRole.SUBMITTER,
    }

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "pesel", "phone_number", "role"]
        extra_kwargs = {
            "role": {"default": User.UserRole.ENTITY_ADMIN},
        }

    def create(self, validated_data):
        request = self.context.get("request")
        from .services import send_activation_email

        user = User.objects.create_user(
            password=None,
            must_change_password=True,
            is_active=False,
            **validated_data,
        )
        send_activation_email(user, request=request)
        return user

    def validate_pesel(self, value: str) -> str:
        digits = value.strip()
        if not digits.isdigit() or len(digits) != 11:
            raise serializers.ValidationError("PESEL musi składać się z 11 cyfr.")
        return digits

    def validate_role(self, value: str) -> str:
        if value not in self.ALLOWED_ROLES:
            allowed = ", ".join(sorted(role for role in self.ALLOWED_ROLES))
            raise serializers.ValidationError(f"Rejestracja dostępna jest tylko dla ról: {allowed}.")
        return value


class ActivateAccountSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        uid = attrs.get("uid")
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Nieprawidłowy identyfikator użytkownika."})

        token = attrs.get("token")
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Nieprawidłowy lub wygasły token aktywacyjny."})

        if user.is_active:
            raise serializers.ValidationError({"uid": "Konto zostało już aktywowane."})

        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")
        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Hasła muszą być identyczne."})

        validate_password(password, user)

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user: User = self.validated_data["user"]
        password = self.validated_data["password"]
        user.set_password(password)
        user.is_active = True
        user.must_change_password = False
        user.save(update_fields=["password", "is_active", "must_change_password"])
        from .services import ensure_initial_access_request

        ensure_initial_access_request(user)
        return user


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError(_("Niepoprawne dane logowania."), code="authorization")
        if not user.is_active:
            raise serializers.ValidationError(_("Konto użytkownika jest nieaktywne."), code="inactive")
        attrs["user"] = user
        return attrs


class RegulatedEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RegulatedEntity
        fields = [
            "id",
            "name",
            "registration_number",
            "sector",
            "address",
            "postal_code",
            "city",
            "country",
            "contact_email",
            "contact_phone",
            "website",
            "status",
            "data_source",
            "last_verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "last_verified_at"]


class EntityMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source="user")
    entity = RegulatedEntitySerializer(read_only=True)
    entity_id = serializers.PrimaryKeyRelatedField(queryset=RegulatedEntity.objects.all(), write_only=True, source="entity")

    class Meta:
        model = EntityMembership
        fields = ["id", "user", "entity", "role", "is_primary", "created_at", "user_id", "entity_id"]
        read_only_fields = ["created_at"]


class AccessRequestAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = AccessRequestAttachment
        fields = ["id", "file", "description", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]

    def get_uploaded_by(self, obj):
        if not obj.uploaded_by:
            return None
        return {
            "id": obj.uploaded_by_id,
            "email": obj.uploaded_by.email,
            "name": f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip(),
        }


class AccessRequestLinePermissionSerializer(serializers.ModelSerializer):
    code_display = serializers.CharField(source="get_code_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    decided_by = serializers.SerializerMethodField()

    class Meta:
        model = AccessRequestLinePermission
        fields = [
            "id",
            "code",
            "code_display",
            "status",
            "status_display",
            "decided_by",
            "decided_at",
            "notes",
        ]
        read_only_fields = [
            "id",
            "code_display",
            "status_display",
            "decided_by",
            "decided_at",
        ]

    def get_decided_by(self, obj):
        if not obj.decided_by:
            return None
        return {
            "id": obj.decided_by_id,
            "email": obj.decided_by.email,
            "name": f"{obj.decided_by.first_name} {obj.decided_by.last_name}".strip(),
        }


class AccessRequestLineSerializer(serializers.ModelSerializer):
    entity = RegulatedEntitySerializer(read_only=True)
    entity_id = serializers.PrimaryKeyRelatedField(
        queryset=RegulatedEntity.objects.all(), write_only=True, source="entity"
    )
    permissions = AccessRequestLinePermissionSerializer(many=True, read_only=True)
    permission_codes = serializers.ListField(
        child=serializers.ChoiceField(choices=AccessRequestLinePermission.PermissionCode.choices),
        write_only=True,
        required=False,
    )

    class Meta:
        model = AccessRequestLine
        fields = [
            "id",
            "entity",
            "entity_id",
            "status",
            "next_actor",
            "contact_email",
            "decision_notes",
            "decided_at",
            "decided_by",
            "permissions",
            "permission_codes",
        ]
        read_only_fields = [
            "id",
            "entity",
            "status",
            "next_actor",
            "decision_notes",
            "decided_at",
            "decided_by",
            "permissions",
        ]


class AccessRequestHistorySerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = AccessRequestHistoryEntry
        fields = ["id", "action", "from_status", "to_status", "payload", "created_at", "actor"]
        read_only_fields = fields

    def get_actor(self, obj):
        if not obj.actor:
            return None
        return {
            "id": obj.actor_id,
            "email": obj.actor.email,
            "name": f"{obj.actor.first_name} {obj.actor.last_name}".strip(),
        }


class AccessRequestMessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequestMessageAttachment
        fields = ["id", "file", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]


class AccessRequestMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    attachments = AccessRequestMessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = AccessRequestMessage
        fields = ["id", "body", "is_internal", "created_at", "sender", "attachments"]
        read_only_fields = ["id", "is_internal", "created_at", "sender", "attachments"]

    def get_sender(self, obj):
        if not obj.sender:
            return None
        return {
            "id": obj.sender_id,
            "email": obj.sender.email,
            "name": f"{obj.sender.first_name} {obj.sender.last_name}".strip(),
        }


class AccessRequestMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField()
    is_internal = serializers.BooleanField(default=False)


class AccessRequestAttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    description = serializers.CharField(required=False, allow_blank=True)


class AccessRequestSerializer(serializers.ModelSerializer):
    requester = UserSerializer(read_only=True)
    requester_pesel_masked = serializers.CharField(read_only=True)
    lines = AccessRequestLineSerializer(many=True, read_only=True)
    attachments = AccessRequestAttachmentSerializer(many=True, read_only=True)
    history = AccessRequestHistorySerializer(many=True, read_only=True)
    messages = AccessRequestMessageSerializer(many=True, read_only=True)
    decided_by = serializers.SerializerMethodField()

    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "reference_code",
            "status",
            "next_actor",
            "handled_by_uknf",
            "requester",
            "requester_first_name",
            "requester_last_name",
            "requester_email",
            "requester_phone",
            "requester_pesel_masked",
            "justification",
            "decision_notes",
            "submitted_at",
            "decided_at",
            "decided_by",
            "created_at",
            "updated_at",
            "lines",
            "attachments",
            "history",
            "messages",
        ]
        read_only_fields = fields

    def get_decided_by(self, obj):
        if not obj.decided_by:
            return None
        return {
            "id": obj.decided_by_id,
            "email": obj.decided_by.email,
            "name": f"{obj.decided_by.first_name} {obj.decided_by.last_name}".strip(),
        }


class AccessRequestLineInputSerializer(serializers.Serializer):
    entity_id = serializers.PrimaryKeyRelatedField(queryset=RegulatedEntity.objects.all(), source="entity")
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    permission_codes = serializers.ListField(
        child=serializers.ChoiceField(choices=AccessRequestLinePermission.PermissionCode.choices)
    )


class AccessRequestUpdateSerializer(serializers.ModelSerializer):
    lines = AccessRequestLineInputSerializer(many=True, required=False)

    class Meta:
        model = AccessRequest
        fields = ["justification", "lines"]

    def update(self, instance: AccessRequest, validated_data):
        lines_data = validated_data.pop("lines", None)
        if "justification" in validated_data:
            instance.justification = validated_data["justification"]
            instance.save(update_fields=["justification", "updated_at"])

        if lines_data is not None:
            self._sync_lines(instance, lines_data)
        instance.refresh_next_actor()
        return instance

    def _sync_lines(self, instance: AccessRequest, lines_data: list[dict]) -> None:
        existing = {line.entity_id: line for line in instance.lines.all()}
        seen_entities: set[int] = set()
        for line_data in lines_data:
            entity = line_data["entity"]
            contact_email = line_data.get("contact_email", "")
            permission_codes = line_data.get("permission_codes", [])
            line = existing.get(entity.id)
            if line is None:
                line = AccessRequestLine.objects.create(request=instance, entity=entity)
            line.contact_email = contact_email
            line.status = AccessRequestLine.LineStatus.PENDING
            line.decision_notes = ""
            line.decided_by = None
            line.decided_at = None
            line.next_actor = AccessRequestLine.NextActor.ENTITY_ADMIN
            line.save()
            self._sync_permissions(line, permission_codes)
            line.save()
            seen_entities.add(entity.id)

        for entity_id, line in existing.items():
            if entity_id not in seen_entities:
                line.permissions.all().delete()
                line.delete()

    def _sync_permissions(self, line: AccessRequestLine, permission_codes: list[str]) -> None:
        existing = {perm.code: perm for perm in line.permissions.all()}
        seen_codes: set[str] = set()
        for code in permission_codes:
            permission = existing.get(code)
            if permission is None:
                AccessRequestLinePermission.objects.create(line=line, code=code)
            else:
                if permission.status != AccessRequestLinePermission.PermissionStatus.REQUESTED:
                    permission.status = AccessRequestLinePermission.PermissionStatus.REQUESTED
                    permission.notes = ""
                    permission.decided_at = None
                    permission.decided_by = None
                    permission.save(update_fields=["status", "notes", "decided_at", "decided_by"])
            seen_codes.add(code)

        for code, permission in existing.items():
            if code not in seen_codes:
                permission.delete()


class AccessRequestDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            AccessRequest.AccessStatus.APPROVED,
            AccessRequest.AccessStatus.BLOCKED,
        ]
    )
    decision_notes = serializers.CharField(required=False, allow_blank=True)


class ContactSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = [
            "id",
            "sender_name",
            "sender_email",
            "subject",
            "message",
            "entity",
            "created_at",
            "handled_by",
            "handled_at",
            "resolution_notes",
        ]
        read_only_fields = ["created_at", "handled_by", "handled_at", "resolution_notes"]


class UserSessionContextSerializer(serializers.ModelSerializer):
    acting_entity = RegulatedEntitySerializer(read_only=True)
    acting_entity_id = serializers.PrimaryKeyRelatedField(
        queryset=RegulatedEntity.objects.all(), write_only=True, source="acting_entity"
    )

    class Meta:
        model = UserSessionContext
        fields = ["id", "acting_entity", "acting_entity_id", "updated_at"]
        read_only_fields = ["id", "updated_at", "acting_entity"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["notify_via_email", "notify_via_sms", "daily_digest", "weekly_digest", "updated_at"]
        read_only_fields = ["updated_at"]
