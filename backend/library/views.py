from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.models import FaqEntry, LibraryDocument
from communication.serializers import FaqEntrySerializer, LibraryDocumentSerializer


class LibraryOverviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        documents = LibraryDocumentSerializer(LibraryDocument.objects.all().order_by("-published_at")[:20], many=True)
        faq = FaqEntrySerializer(FaqEntry.objects.filter(is_active=True).order_by("order")[:20], many=True)
        return Response({"documents": documents.data, "faq": faq.data})


class LibrarySearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").lower()
        documents_qs = LibraryDocument.objects.all()
        if query:
            documents_qs = documents_qs.filter(title__icontains=query)
        return Response(
            {
                "results": LibraryDocumentSerializer(documents_qs.order_by("-published_at")[:50], many=True).data,
                "query": query,
            }
        )
