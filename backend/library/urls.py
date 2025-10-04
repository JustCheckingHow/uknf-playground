from __future__ import annotations

from django.urls import path

from .views import (
    LibraryDocumentDetailView,
    LibraryDocumentUploadView,
    LibraryOverviewView,
    LibraryQuestionAnswerView,
    LibrarySearchView,
)

urlpatterns = [
    path("overview", LibraryOverviewView.as_view(), name="library-overview"),
    path("search", LibrarySearchView.as_view(), name="library-search"),
    path("documents", LibraryDocumentUploadView.as_view(), name="library-document-upload"),
    path("documents/<int:document_id>", LibraryDocumentDetailView.as_view(), name="library-document-detail"),
    path("qa", LibraryQuestionAnswerView.as_view(), name="library-question"),
]
