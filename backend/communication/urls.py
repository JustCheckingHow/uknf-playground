from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnnouncementViewSet,
    CaseViewSet,
    FaqViewSet,
    LibraryDocumentViewSet,
    MessageThreadViewSet,
    ReportViewSet,
)

router = DefaultRouter()
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"cases", CaseViewSet, basename="case")
router.register(r"messages", MessageThreadViewSet, basename="thread")
router.register(r"announcements", AnnouncementViewSet, basename="announcement")
router.register(r"library", LibraryDocumentViewSet, basename="library-document")
router.register(r"faq", FaqViewSet, basename="faq")

urlpatterns = [
    path("", include(router.urls)),
]
