from __future__ import annotations

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.models import Token

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

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
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
    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "role", "phone_number"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 12},
            "role": {"default": User.UserRole.ENTITY_ADMIN},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save(update_fields=["password"])
        Token.objects.get_or_create(user=user)
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
