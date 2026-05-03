"""
retriever.py
------------
Combines :class:`~embedder.LocalEmbedder` and
:class:`~vector_store.AirportVectorStore` to turn a raw user query string
into a ranked list of relevant airport document chunks.
"""

from __future__ import annotations

from typing import Any

from backend.app.core.rag.embedder import LocalEmbedder
from backend.app.core.rag.vector_store import AirportVectorStore


class AirportRetriever:
    """Retrieves the most relevant airport knowledge chunks for a query.

    Parameters
    ----------
    embedder : LocalEmbedder
        Pre-initialised embedding model instance.
    vector_store : AirportVectorStore
        Pre-initialised ChromaDB vector store instance.

    Examples
    --------
    >>> retriever = AirportRetriever(embedder, store)
    >>> results = retriever.retrieve("Where is Gate B12?", top_k=3)
    >>> for r in results:
    ...     print(r["score"], r["text"][:60])
    """

    def __init__(
        self,
        embedder: LocalEmbedder,
        vector_store: AirportVectorStore,
    ) -> None:
        """Bind the embedder and vector store used for retrieval.

        Parameters
        ----------
        embedder : LocalEmbedder
            The text embedding model.
        vector_store : AirportVectorStore
            The vector store to query.
        """
        self._embedder: LocalEmbedder = embedder
        self._store: AirportVectorStore = vector_store

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Embed *query* and return the top-*k* most relevant chunks.

        Parameters
        ----------
        query : str
            Natural-language query from the user.
        top_k : int
            Number of chunks to return (capped by the store's document
            count).

        Returns
        -------
        list[dict]
            Ranked list of ``{"text": str, "metadata": dict,
            "score": float}`` dicts, ordered from most to least similar.

        Raises
        ------
        ValueError
            If *query* is empty or whitespace-only.
        RuntimeError
            If the vector store is empty (``load_and_index`` has not been
            called yet).
        """
        query = query.strip()
        if not query:
            raise ValueError("retrieve() received an empty query string.")

        if self._store.count() == 0:
            raise RuntimeError(
                "The vector store is empty.  Call pipeline.load_and_index() "
                "before issuing queries."
            )

        query_vector: list[float] = self._embedder.embed_query(query)
        results: list[dict[str, Any]] = self._store.search(
            query_embedding=query_vector,
            top_k=top_k,
        )
        return results
