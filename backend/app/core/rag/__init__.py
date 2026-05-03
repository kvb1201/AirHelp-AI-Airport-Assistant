"""
RAG (Retrieval-Augmented Generation) package for the AI Airport Companion.

Exports the top-level AirportRAGPipeline so callers can do:
    from backend.app.core.rag import AirportRAGPipeline
"""

from backend.app.core.rag.pipeline import AirportRAGPipeline

__all__ = ["AirportRAGPipeline"]
