from __future__ import annotations

from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from accounts.models import UserGroup
from .models import MessageThread

User = get_user_model()


class MessageThreadFilter(filters.FilterSet):
    updated_after = filters.DateFilter(field_name="updated_at", lookup_expr="date__gte")
    updated_before = filters.DateFilter(field_name="updated_at", lookup_expr="date__lte")
    group = filters.ModelChoiceFilter(field_name="target_group", queryset=UserGroup.objects.all())
    user = filters.ModelChoiceFilter(field_name="target_user", queryset=User.objects.all())
    target_type = filters.CharFilter(method="filter_target_type")

    class Meta:
        model = MessageThread
        fields = ["group", "user"]

    def filter_target_type(self, queryset, name, value):
        if value == "group":
            return queryset.filter(target_group__isnull=False)
        if value == "user":
            return queryset.filter(target_user__isnull=False)
        return queryset
