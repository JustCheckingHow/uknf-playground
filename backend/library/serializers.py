from __future__ import annotations

from pathlib import Path

from rest_framework import serializers

from communication.models import LibraryDocument
from .services import compute_text_embedding, extract_text_from_file


class LibraryDocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = LibraryDocument
        fields = [
            "title",
            "category",
            "version",
            "published_at",
            "description",
            "file",
            "is_mandatory",
        ]
        extra_kwargs = {
            "title": {"required": False, "allow_blank": True},
            "description": {"required": False, "allow_blank": True, "default": ""},
            "version": {"required": False, "default": "1.0"},
            "published_at": {"required": False},
        }

    def create(self, validated_data):
        uploaded_file = validated_data.pop("file")
        validated_data.setdefault("description", "")

        if not validated_data.get("title"):
            filename = Path(uploaded_file.name).stem or uploaded_file.name
            validated_data["title"] = filename

        indexed_text = extract_text_from_file(uploaded_file)
        content_parts = [validated_data.get("description", "").strip(), indexed_text.strip()]
        combined_content = "\n\n".join(part for part in content_parts if part)

        document = LibraryDocument.objects.create(file=uploaded_file, **validated_data)

        update_fields: list[str] = []
        if combined_content:
            document.content = combined_content
            update_fields.append("content")

        embedding_payload = "\n\n".join(
            part for part in [document.title, combined_content or indexed_text] if part
        )
        embedding = compute_text_embedding(embedding_payload)
        if embedding:
            document.embedding = embedding
            update_fields.append("embedding")

        if update_fields:
            document.save(update_fields=update_fields)
        return document


class LibraryQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
