from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.models import FaqEntry, LibraryDocument
from communication.serializers import FaqEntrySerializer, LibraryDocumentSerializer
from .serializers import LibraryDocumentUploadSerializer, LibraryQuestionSerializer
from .services import generate_library_answer


logger = logging.getLogger(__name__)


class LibraryOverviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        documents = LibraryDocumentSerializer(
            LibraryDocument.objects.all().order_by("-published_at")[:20],
            many=True,
            context={"request": request},
        )
        faq = FaqEntrySerializer(
            FaqEntry.objects.filter(is_active=True).order_by("order")[:20],
            many=True,
        )
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
                "results": LibraryDocumentSerializer(
                    documents_qs.order_by("-published_at")[:50],
                    many=True,
                    context={"request": request},
                ).data,
                "query": query,
            }
        )


class LibraryDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = LibraryDocumentUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        response_serializer = LibraryDocumentSerializer(document, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class LibraryQuestionAnswerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LibraryQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        try:
            answer, sources = generate_library_answer(question)
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
