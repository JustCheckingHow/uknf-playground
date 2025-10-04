from __future__ import annotations

from django.urls import path

from .views import LibraryOverviewView, LibrarySearchView

urlpatterns = [
    path("overview", LibraryOverviewView.as_view(), name="library-overview"),
    path("search", LibrarySearchView.as_view(), name="library-search"),
]
