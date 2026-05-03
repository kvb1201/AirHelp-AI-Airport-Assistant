"""
RAG (Retrieval-Augmented Generation) package for the AI Airport Companion.

Exports the top-level AirportRAGPipeline so callers can do:
    from app.core.rag import AirportRAGPipeline
"""

from app.core.rag.pipeline import AirportRAGPipeline
__all__ = ["AirportRAGPipeline"]
