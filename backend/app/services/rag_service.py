"""Structured-first retrieval for the airport assistant."""

from __future__ import annotations

from app.core.knowledge_base.repository import KnowledgeBaseRepository


_repository = KnowledgeBaseRepository()


def get_relevant_context(query: str) -> dict:
    """Return both structured matches and text chunks for prompt grounding."""
    places = _repository.search_places(query, limit=5)
    chunks = _repository.get_relevant_chunks(query, limit=5)

    return {
        "places": [place.model_dump() for place in places],
        "chunks": chunks,
    }


def build_knowledge_base() -> None:
    """Compile the normalized airport collections from the raw project data."""
    _repository.ensure_compiled()

