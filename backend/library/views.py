from __future__ import annotations

import logging

from django.db.models import Q
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.models import FaqEntry, LibraryDocument
from communication.serializers import FaqEntrySerializer, LibraryDocumentSerializer
from accounts.permissions import IsInternalUser

from .serializers import LibraryDocumentUploadSerializer, LibraryQuestionSerializer
from .services import generate_library_answer
from .utils import filter_documents_for_user


logger = logging.getLogger(__name__)


class LibraryOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        documents_qs = filter_documents_for_user(
            LibraryDocument.objects.all().order_by("-published_at"),
            request.user,
        )
        documents = LibraryDocumentSerializer(
            documents_qs[:20],
            many=True,
            context={"request": request},
        )
        faq = FaqEntrySerializer(
            FaqEntry.objects.filter(is_active=True).order_by("order")[:20],
            many=True,
        )
        return Response({"documents": documents.data, "faq": faq.data})


class LibrarySearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").lower()
        documents_qs = filter_documents_for_user(
            LibraryDocument.objects.all(),
            request.user,
        )
        if query:
            documents_qs = documents_qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(document_url__icontains=query)
                | Q(file__icontains=query)
            )
        return Response(
            {
                "results": LibraryDocumentSerializer(
                    documents_qs.order_by("-published_at")[:50],
                    many=True,
                    context={"request": request},
                ).data,
                "query": query,
            }
        )


class LibraryDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated, IsInternalUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = LibraryDocumentUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        response_serializer = LibraryDocumentSerializer(document, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class LibraryDocumentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsInternalUser]

    def delete(self, request, document_id: int, *args, **kwargs):
        try:
            document = LibraryDocument.objects.get(pk=document_id)
        except LibraryDocument.DoesNotExist:
            return Response({"detail": "Nie znaleziono dokumentu."}, status=status.HTTP_404_NOT_FOUND)

        stored_file = document.file
        stored_file_name = stored_file.name if stored_file else ""
        storage = stored_file.storage if stored_file else None

        document.delete()

        if storage and stored_file_name:
            try:
                storage.delete(stored_file_name)
            except Exception as exc:  # pragma: no cover - storage backend safety
                logger.warning("Nie udało się usunąć pliku dokumentu %s: %s", document_id, exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class LibraryQuestionAnswerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LibraryQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        try:
            answer, sources = generate_library_answer(question, request.user)
        except RuntimeError as exc:
            logger.warning("Library QA unavailable: %s", exc)
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Library QA failed")
            return Response(
                {"detail": "Nie udało się uzyskać odpowiedzi. Spróbuj ponownie później."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        sources_payload = LibraryDocumentSerializer(
            sources,
            many=True,
            context={"request": request},
        ).data

        return Response(
            {
                "question": question,
                "answer": answer,
                "sources": sources_payload,
            }
        )
