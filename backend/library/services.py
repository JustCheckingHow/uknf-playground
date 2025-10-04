from __future__ import annotations

import logging
import math
import re
from functools import lru_cache
from typing import Iterable, Sequence

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Q

from communication.models import LibraryDocument

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency during import
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

except ImportError:  # pragma: no cover
    Agent = None  # type: ignore[assignment]
    OpenAIChatModel = None  # type: ignore[assignment]

try:  # pragma: no cover
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


MAX_BYTES_TO_INDEX = 200_000
MAX_CHARS_PER_DOCUMENT = 2000
MAX_DOCUMENTS = 5
MAX_EMBEDDING_CHARS = 8_000
SIMILARITY_FALLBACK_LIMIT = 2

_embedding_client: OpenAI | None = None


def extract_text_from_file(uploaded_file: UploadedFile) -> str:
    """Return a UTF-8 decoded preview of the uploaded file for lightweight search."""

    if uploaded_file.multiple_chunks():
        data = b"".join(chunk for chunk in uploaded_file.chunks())
    else:
        data = uploaded_file.read()

    if len(data) > MAX_BYTES_TO_INDEX:
        logger.debug(
            "Truncating uploaded file for indexing: %s > %s bytes",
            len(data),
            MAX_BYTES_TO_INDEX,
        )
        data = data[:MAX_BYTES_TO_INDEX]

    text = data.decode("utf-8", errors="ignore").strip()
    uploaded_file.seek(0)
    return text


def _tokenize_query(query: str) -> Iterable[str]:
    for token in re.split(r"\W+", query.lower()):
        if len(token) > 2:
            yield token


def select_relevant_documents(question: str) -> list[LibraryDocument]:
    semantic_matches = _semantic_search(question)
    if semantic_matches:
        return semantic_matches
    return _fallback_documents(question)


def _semantic_search(question: str) -> list[LibraryDocument]:
    embedding = compute_text_embedding(question)
    if not embedding:
        return []

    candidate_rows = list(
        LibraryDocument.objects.exclude(embedding__isnull=True)
        .exclude(embedding=[])
        .values("id", "embedding")
    )
    if not candidate_rows:
        return []

    scored_ids: list[tuple[float, int]] = []
    for row in candidate_rows:
        vector = row.get("embedding") or []
        if not isinstance(vector, (list, tuple)) or not vector:
            continue
        similarity = _cosine_similarity(embedding, vector)
        scored_ids.append((similarity, row["id"]))

    if not scored_ids:
        return []

    scored_ids.sort(key=lambda item: item[0], reverse=True)
    top_ids = [item[1] for item in scored_ids[:MAX_DOCUMENTS]]
    documents_by_id = LibraryDocument.objects.in_bulk(top_ids)
    return [documents_by_id[doc_id] for doc_id in top_ids if doc_id in documents_by_id]


def _fallback_documents(question: str) -> list[LibraryDocument]:
    tokens = list(_tokenize_query(question))
    queryset = LibraryDocument.objects.all()
    if tokens:
        query = Q()
        for token in tokens:
            query |= Q(title__icontains=token)
            query |= Q(description__icontains=token)
            query |= Q(content__icontains=token)
            query |= Q(document_url__icontains=token)
            query |= Q(file__icontains=token)
        queryset = queryset.filter(query)
    documents = list(queryset.order_by("-published_at")[:MAX_DOCUMENTS])
    if not documents:
        documents = list(LibraryDocument.objects.order_by("-published_at")[:SIMILARITY_FALLBACK_LIMIT])
    return documents


def build_document_context(documents: Sequence[LibraryDocument]) -> str:
    parts: list[str] = []
    for document in documents:
        snippet = (document.content or "")[:MAX_CHARS_PER_DOCUMENT]
        description_line = document.description or "(brak opisu)"
        parts.append(
            "\n".join(
                [
                    f"Tytuł: {document.title}",
                    f"Kategoria: {document.get_category_display()}",
                    f"Opis: {description_line}",
                    "Treść fragmentu:",
                    snippet or "(Brak zindeksowanej treści)",
                ]
            )
        )
    return "\n\n---\n\n".join(parts)


def get_embedding_client() -> OpenAI:
    global _embedding_client
    if _embedding_client is None:
        if OpenAI is None:
            raise RuntimeError("Pakiet 'openai' nie jest dostępny.")
        if not getattr(settings, "OPENAI_API_KEY", None):
            raise RuntimeError("Brak klucza OPENAI_API_KEY w konfiguracji.")
        _embedding_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _embedding_client


def compute_text_embedding(text: str) -> list[float] | None:
    payload = (text or "").strip()
    if not payload:
        return None
    payload = payload[:MAX_EMBEDDING_CHARS]
    try:
        client = get_embedding_client()
    except RuntimeError as exc:
        logger.warning("Embeddings unavailable: %s", exc)
        return None

    model_name = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    try:
        response = client.embeddings.create(model=model_name, input=payload)
    except Exception as exc:  # pragma: no cover - network call
        logger.warning("Nie udało się wygenerować wektora osadzeń biblioteki: %s", exc)
        return None

    data = getattr(response, "data", None)
    if not data:
        return None
    embedding = getattr(data[0], "embedding", None)
    if not embedding:
        return None
    return list(embedding)


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    if length == 0:
        return 0.0
    dot = sum(left[i] * right[i] for i in range(length))
    left_norm = math.sqrt(sum(left[i] * left[i] for i in range(length)))
    right_norm = math.sqrt(sum(right[i] * right[i] for i in range(length)))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


@lru_cache(maxsize=1)
def get_library_agent() -> Agent:
    if Agent is None or OpenAIChatModel is None:
        raise RuntimeError("Pakiet 'pydantic_ai' nie jest dostępny.")
    if not getattr(settings, "OPENAI_API_KEY", None):
        raise RuntimeError("Brak klucza OPENAI_API_KEY w konfiguracji.")

    model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    return Agent(
        OpenAIChatModel(
            model_name, provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        ),
        system_prompt=(
            "Jesteś ekspertem UKNF pomagającym odpowiadać na pytania na podstawie dokumentów. "
            "Udzielaj odpowiedzi po polsku, cytuj istotne fragmenty i jasno zaznaczaj, gdy informacje są niepewne."
        ),
    )


def generate_library_answer(question: str) -> tuple[str, list[LibraryDocument]]:
    documents = select_relevant_documents(question)
    context_text = build_document_context(documents)
    agent = get_library_agent()
    prompt = (
        "Odpowiedz na pytanie użytkownika, korzystając wyłącznie z przekazanych fragmentów dokumentów biblioteki UKNF."
        " Jeśli dokumenty nie zawierają odpowiedzi, poinformuj użytkownika o braku danych.\n\n"
        f"Pytanie: {question.strip()}\n\n"
        f"Dokumenty:\n{context_text}\n"
    )
    result = agent.run_sync(prompt)
    answer = getattr(result, "output_text", str(result))
    return answer.strip(), documents


__all__ = ["compute_text_embedding", "extract_text_from_file", "generate_library_answer"]
