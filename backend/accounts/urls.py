from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivateAccountView,
    AccessRequestViewSet,
    ContactSubmissionViewSet,
    EntityMembershipViewSet,
    LoginView,
    LogoutView,
    NotificationPreferenceView,
    ProfileView,
    RegulatedEntityViewSet,
    RegisterView,
    RoleCatalogView,
    SessionContextView,
    UserDirectoryView,
    UserGroupViewSet,
)

router = DefaultRouter()
router.register(r"entities", RegulatedEntityViewSet)
router.register(r"memberships", EntityMembershipViewSet, basename="membership")
router.register(r"access-requests", AccessRequestViewSet, basename="access-request")
router.register(r"contacts", ContactSubmissionViewSet, basename="contact")
router.register(r"users", UserDirectoryView, basename="user-directory")
router.register(r"user-groups", UserGroupViewSet, basename="user-group")

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("activate", ActivateAccountView.as_view(), name="activate"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("session", SessionContextView.as_view(), name="session"),
    path("preferences", NotificationPreferenceView.as_view(), name="preferences"),
    path("roles", RoleCatalogView.as_view(), name="roles"),
    path("", include(router.urls)),
]
