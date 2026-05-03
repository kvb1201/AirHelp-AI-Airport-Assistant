"""
embedder.py
-----------
Local text embedding using the `sentence-transformers` library.

Model: all-MiniLM-L6-v2
  - ~22 M parameters, 384-dimensional dense embeddings.
  - Runs fully offline once the model weights have been downloaded.
  - Fast enough for real-time query embedding on CPU.
"""

from __future__ import annotations

from typing import Any


class LocalEmbedder:
    """Wrapper around a SentenceTransformer model for text embedding.

    Parameters
    ----------
    model_name : str
        HuggingFace model identifier.  Defaults to ``all-MiniLM-L6-v2``.
        The first call will trigger an automatic download; subsequent
        calls use the locally cached weights.

    Examples
    --------
    >>> embedder = LocalEmbedder()
    >>> vecs = embedder.embed_texts(["Hello airport!", "Gate B12 is nearby."])
    >>> len(vecs[0])
    384
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialise the embedder and load the sentence-transformer model.

        Parameters
        ----------
        model_name : str
            Name (or local path) of the SentenceTransformer model to load.
        """
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from exc

        self.model_name: str = model_name
        print(f"[Embedder] Loading model '{model_name}' …")
        self._model: Any = SentenceTransformer(model_name)
        print(f"[Embedder] Model loaded successfully.")

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return their vector representations.

        Parameters
        ----------
        texts : list[str]
            The input strings to embed.

        Returns
        -------
        list[list[float]]
            A list of embedding vectors, one per input text.  Each vector
            has length equal to the model's output dimension (384 for
            all-MiniLM-L6-v2).

        Raises
        ------
        ValueError
            If *texts* is empty.
        """
        if not texts:
            raise ValueError("embed_texts() received an empty list.")

        embeddings = self._model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string.

        This is a convenience wrapper around :meth:`embed_texts` that
        accepts a single string instead of a list.

        Parameters
        ----------
        query : str
            The search query to embed.

        Returns
        -------
        list[float]
            A single embedding vector.
        """
        if not query or not query.strip():
            raise ValueError("embed_query() received an empty query string.")

        return self.embed_texts([query])[0]
