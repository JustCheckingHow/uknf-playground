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
    pesel_masked = serializers.CharField(source="pesel_masked", read_only=True)

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


class AccessRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "entity_name",
            "entity_registration_number",
            "requester_name",
            "requester_email",
            "requester_phone",
            "requested_role",
            "justification",
            "status",
            "submitted_at",
            "reviewed_at",
            "reviewed_by",
            "decision_notes",
        ]
        read_only_fields = ["submitted_at", "reviewed_at", "reviewed_by", "status"]


class AccessRequestDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        AccessRequest.AccessStatus.APPROVED,
        AccessRequest.AccessStatus.REJECTED,
    ])
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
