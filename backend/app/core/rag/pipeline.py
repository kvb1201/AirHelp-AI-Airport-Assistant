"""
pipeline.py
-----------
Top-level orchestration class for the AI Airport Companion RAG pipeline.

Flow
----
1. ``load_and_index()``
   JSON → Loader → Chunker → Embedder → VectorStore

2. ``query(user_query)``
   Query → Embedder → VectorStore → Retriever → PromptBuilder → Ollama → Answer

All inference is fully local:
  - Embeddings: sentence-transformers (all-MiniLM-L6-v2)
  - LLM:        Ollama (default model: gemma)
  - Vector DB:  ChromaDB (persistent local storage)
"""

from __future__ import annotations

import json
import sys
from typing import Any

import requests  # type: ignore[import]

from app.core.rag.loader import load_airport_data
from app.core.rag.chunker import chunk_documents
from app.core.rag.embedder import LocalEmbedder
from app.core.rag.vector_store import AirportVectorStore
from app.core.rag.retriever import AirportRetriever
from app.core.rag.prompt_builder import build_prompt


class AirportRAGPipeline:
    """End-to-end RAG pipeline for the AI Airport Companion.

    Parameters
    ----------
    json_path : str
        Path to the airport knowledge-base JSON file.
    ollama_model : str
        Name of the Ollama model to use for generation (default: ``"gemma"``).
    ollama_base_url : str
        Base URL of the running Ollama server
        (default: ``"http://localhost:11434"``).
    persist_dir : str
        Directory used by ChromaDB to persist vector data
        (default: ``"./chroma_db"``).

    Examples
    --------
    >>> pipeline = AirportRAGPipeline(json_path="airport_data.json")
    >>> pipeline.load_and_index()
    >>> answer = pipeline.query("Where is Gate B12?")
    >>> print(answer)
    """

    def __init__(
        self,
        json_path: str,
        ollama_model: str = "gemma:2b",
        ollama_base_url: str = "http://localhost:11434",
        persist_dir: str = "./chroma_db",
    ) -> None:
        """Wire up all pipeline components.

        Parameters
        ----------
        json_path : str
            Absolute or relative path to ``airport_data.json``.
        ollama_model : str
            Ollama model tag (e.g. ``"gemma"``, ``"llama3"``).
        ollama_base_url : str
            URL where Ollama is listening.
        persist_dir : str
            ChromaDB persistence directory.
        """
        self.json_path: str = json_path
        self.ollama_model: str = ollama_model
        self.ollama_base_url: str = ollama_base_url.rstrip("/")

        # Initialise sub-components.
        self._embedder: LocalEmbedder = LocalEmbedder()
        self._vector_store: AirportVectorStore = AirportVectorStore(
            persist_dir=persist_dir
        )
        self._retriever: AirportRetriever = AirportRetriever(
            embedder=self._embedder,
            vector_store=self._vector_store,
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def load_and_index(self) -> None:
        """Load the JSON knowledge base, chunk, embed, and index it.

        Steps
        -----
        1. Load documents from the JSON file via :func:`~loader.load_airport_data`.
        2. Chunk documents via :func:`~chunker.chunk_documents`.
        3. Embed all chunks via :class:`~embedder.LocalEmbedder`.
        4. Store embeddings in :class:`~vector_store.AirportVectorStore`.

        Progress is printed to stdout at each step.

        Raises
        ------
        FileNotFoundError
            If :attr:`json_path` does not exist.
        ValueError
            If the JSON file is malformed.
        """
        # ---- Step 1: Load -----------------------------------------------
        print(f"\n[Pipeline] Step 1/4 — Loading data from '{self.json_path}' …")
        try:
            documents = load_airport_data(self.json_path)
        except FileNotFoundError as exc:
            print(f"[Pipeline] ERROR: {exc}", file=sys.stderr)
            raise
        except ValueError as exc:
            print(f"[Pipeline] ERROR: {exc}", file=sys.stderr)
            raise
        print(f"[Pipeline]   ✓ Loaded {len(documents)} documents.")

        # ---- Step 2: Chunk ----------------------------------------------
        print("[Pipeline] Step 2/4 — Chunking documents …")
        chunks = chunk_documents(documents, chunk_size=500, overlap=50)
        print(f"[Pipeline]   ✓ Created {len(chunks)} chunks.")

        # ---- Step 3: Embed ----------------------------------------------
        print("[Pipeline] Step 3/4 — Embedding chunks (this may take a moment) …")
        texts: list[str] = [c["text"] for c in chunks]
        metadatas: list[dict] = [c["metadata"] for c in chunks]

        embeddings: list[list[float]] = self._embedder.embed_texts(texts)
        print(f"[Pipeline]   ✓ Generated {len(embeddings)} embeddings "
              f"(dim={len(embeddings[0]) if embeddings else 0}).")

        # ---- Step 4: Store ----------------------------------------------
        print("[Pipeline] Step 4/4 — Storing in ChromaDB …")
        self._vector_store.clear()           # start fresh on re-index
        self._vector_store.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        print(f"[Pipeline]   ✓ Indexed {self._vector_store.count()} chunks.\n")
        print("[Pipeline] ✅ Knowledge base indexed and ready!")

    def query(self, user_query: str, top_k: int = 5) -> str:
        """Answer a passenger question using the RAG pipeline.

        Parameters
        ----------
        user_query : str
            The natural-language question from the user.
        top_k : int
            Number of context chunks to retrieve before prompting the LLM.

        Returns
        -------
        str
            The LLM-generated answer string.

        Raises
        ------
        RuntimeError
            If the vector store is empty (index first).
        ConnectionError
            If Ollama is not reachable.
        """
        user_query = user_query.strip()
        if not user_query:
            return "Please provide a question."

        if not self.is_indexed():
            raise RuntimeError(
                "The knowledge base has not been indexed yet.  "
                "Call load_and_index() first."
            )

        # Retrieve relevant context.
        try:
            retrieved = self._retriever.retrieve(user_query, top_k=top_k)
        except Exception as exc:  # noqa: BLE001
            print(f"[Pipeline] Retrieval error: {exc}", file=sys.stderr)
            retrieved = []

        if not retrieved:
            return (
                "I don't have that information right now, "
                "please check the airport information desk."
            )

        # Build prompt and call Ollama.
        prompt = build_prompt(query=user_query, retrieved_chunks=retrieved)
        answer = self._call_ollama(prompt)
        return answer

    def is_indexed(self) -> bool:
        """Return ``True`` if the vector store contains at least one document.

        Returns
        -------
        bool
        """
        return self._vector_store.count() > 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_ollama(self, prompt: str) -> str:
        """Send *prompt* to Ollama and return the generated text.

        Parameters
        ----------
        prompt : str
            The fully-assembled prompt string.

        Returns
        -------
        str
            The ``"response"`` field from the Ollama JSON response.

        Raises
        ------
        ConnectionError
            If the Ollama server is unreachable or returns an error status.
        """
        url = f"{self.ollama_base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError(
                f"Could not connect to Ollama at '{self.ollama_base_url}'. "
                "Make sure Ollama is running (`ollama serve`) and the model "
                f"'{self.ollama_model}' is available (`ollama pull {self.ollama_model}`)."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise ConnectionError(
                f"Ollama request timed out after 120 seconds.  "
                "The model may be loading — try again in a moment."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise ConnectionError(
                f"Ollama returned HTTP {response.status_code}: {response.text}"
            ) from exc

        try:
            data: dict[str, Any] = response.json()
        except json.JSONDecodeError as exc:
            raise ConnectionError(
                f"Ollama returned non-JSON response: {response.text[:200]}"
            ) from exc

        answer: str = data.get("response", "").strip()
        if not answer:
            answer = (
                "I received an empty response from the language model.  "
                "Please try again."
            )
        return answer


# ---------------------------------------------------------------------------
# Standalone demo / smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    JSON_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "airport_data.json",
    )

    print("=" * 60)
    print("  AeroGuide RAG Pipeline — Smoke Test")
    print("=" * 60)

    pipeline = AirportRAGPipeline(
        json_path=JSON_PATH,
        ollama_model="gemma:2b",
    )

    pipeline.load_and_index()

    test_queries = [
        "Where is Gate B12 and how do I get there?",
        "What food options are available near Terminal 2?",
        "Are there any offers at the duty-free shops?",
    ]

    for i, q in enumerate(test_queries, 1):
        print(f"\n{'─' * 60}")
        print(f"  Query {i}: {q}")
        print("─" * 60)
        try:
            answer = pipeline.query(q)
            print(f"  AeroGuide: {answer}")
        except ConnectionError as e:
            print(f"  [Ollama not available] {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  [Error] {e}")

    print(f"\n{'=' * 60}")
    print("  Smoke test complete.")
    print("=" * 60)
