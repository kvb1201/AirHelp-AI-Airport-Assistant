"""
vector_store.py
---------------
ChromaDB-backed persistent vector store for the airport knowledge base.

Storage location: ``./chroma_db`` (relative to the working directory, or
overridden via *persist_dir*).

ChromaDB persists data automatically between process restarts, so
``load_and_index()`` only needs to be called once (or whenever the
knowledge base changes).
"""

from __future__ import annotations

from typing import Any


class AirportVectorStore:
    """ChromaDB-based persistent vector store for airport documents.

    Parameters
    ----------
    collection_name : str
        Name of the ChromaDB collection to use.
    persist_dir : str
        Directory on disk where ChromaDB will store its data.

    Examples
    --------
    >>> store = AirportVectorStore()
    >>> store.add_documents(texts, embeddings, metadatas)
    >>> results = store.search(query_embedding, top_k=3)
    """

    def __init__(
        self,
        collection_name: str = "airport_knowledge",
        persist_dir: str = "./chroma_db",
    ) -> None:
        """Initialise ChromaDB client and get-or-create the collection.

        Parameters
        ----------
        collection_name : str
            ChromaDB collection name.
        persist_dir : str
            Path to the local persistence directory.
        """
        try:
            import chromadb  # type: ignore[import]
            from chromadb.config import Settings  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "chromadb is not installed. Run: pip install chromadb"
            ) from exc

        self.collection_name: str = collection_name
        self.persist_dir: str = persist_dir

        # PersistentClient keeps data on disk automatically.
        self._client: Any = chromadb.PersistentClient(path=persist_dir)
        self._collection: Any = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},   # cosine similarity
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def add_documents(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add documents (with pre-computed embeddings) to the collection.

        Parameters
        ----------
        texts : list[str]
            The raw text of each document chunk.
        embeddings : list[list[float]]
            Corresponding embedding vectors (one per text).
        metadatas : list[dict]
            Per-document metadata dicts (one per text).

        Raises
        ------
        ValueError
            If the three lists have different lengths.
        """
        if not (len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError(
                f"Lengths of texts ({len(texts)}), embeddings ({len(embeddings)}), "
                f"and metadatas ({len(metadatas)}) must all match."
            )

        # Build unique IDs based on position (stable across re-runs).
        ids = [f"doc_{i}" for i in range(len(texts))]

        # Sanitise metadata: ChromaDB only accepts str/int/float/bool values.
        clean_meta = [_sanitise_metadata(m) for m in metadatas]

        # Upsert to avoid duplicate-key errors on repeated indexing.
        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=clean_meta,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Return the top-k most similar documents to *query_embedding*.

        Parameters
        ----------
        query_embedding : list[float]
            The query vector produced by :class:`~embedder.LocalEmbedder`.
        top_k : int
            Number of results to return.

        Returns
        -------
        list[dict]
            Each element has keys ``"text"``, ``"metadata"``, and
            ``"score"`` (cosine similarity; higher is more similar).
        """
        if self.count() == 0:
            return []

        n_results = min(top_k, self.count())
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        output: list[dict[str, Any]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            # ChromaDB returns squared L2 or cosine distance (0 = identical).
            # Convert distance → similarity score (1 = perfect match).
            score = round(1.0 - float(dist), 4)
            output.append({
                "text": doc,
                "metadata": meta,
                "score": score,
            })

        return output

    def clear(self) -> None:
        """Delete all documents from the collection.

        The collection itself is preserved (same name and settings).
        This is useful when you want to re-index from scratch.
        """
        self._client.delete_collection(self.collection_name)
        import chromadb  # type: ignore[import]
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Return the total number of documents currently in the store.

        Returns
        -------
        int
        """
        return self._collection.count()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _sanitise_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Convert metadata values to types ChromaDB accepts (str/int/float/bool)."""
    clean: dict[str, Any] = {}
    for key, value in meta.items():
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean
