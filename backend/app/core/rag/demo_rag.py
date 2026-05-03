"""
demo_rag.py
-----------
Standalone demo script to test the AeroGuide RAG pipeline end-to-end.

Usage (from the project root):
    python backend/app/core/rag/demo_rag.py

Prerequisites:
    1. Install dependencies:
           pip install sentence-transformers chromadb requests
    2. Start Ollama with the gemma model:
           ollama serve          # in one terminal
           ollama pull gemma     # first time only
    3. Ensure airport_data.json is in the same directory as this script
       (it is created by default alongside pipeline.py).

What this demo does:
    - Initialises all RAG components individually so you can inspect each step.
    - Loads and flattens the JSON knowledge base.
    - Chunks the documents.
    - Embeds the chunks.
    - Stores them in ChromaDB.
    - Runs five test queries and prints results.
    - Falls back gracefully if Ollama is not running (prints retrieved context
      instead of the LLM answer).
"""

from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Make sure the project root is on the Python path so imports work whether
# the script is executed directly or via `python -m`.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from backend.app.core.rag.loader import load_airport_data
from backend.app.core.rag.chunker import chunk_documents
from backend.app.core.rag.embedder import LocalEmbedder
from backend.app.core.rag.vector_store import AirportVectorStore
from backend.app.core.rag.retriever import AirportRetriever
from backend.app.core.rag.prompt_builder import build_prompt
from backend.app.core.rag.pipeline import AirportRAGPipeline


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "airport_data.json")
PERSIST_DIR = os.path.join(SCRIPT_DIR, "chroma_db_demo")
OLLAMA_MODEL = "gemma:2b"
OLLAMA_URL = "http://localhost:11434"


# ---------------------------------------------------------------------------
# Helper: pretty section separator
# ---------------------------------------------------------------------------
def _section(title: str) -> None:
    print(f"\n{'═' * 64}")
    print(f"  {title}")
    print("═" * 64)


def _step(number: int, description: str) -> None:
    print(f"\n  [{number}] {description}")
    print("  " + "─" * 58)


# ---------------------------------------------------------------------------
# Demo: component-level walkthrough
# ---------------------------------------------------------------------------
def demo_components() -> None:
    """Walk through each RAG component individually."""

    _section("COMPONENT-LEVEL DEMO")

    # ---- Step 1: Loader ---------------------------------------------------
    _step(1, "Loading airport JSON data …")
    docs = load_airport_data(JSON_PATH)
    print(f"  ✓ Loaded {len(docs)} raw documents.")
    print(f"  Categories: {set(d['metadata']['category'] for d in docs)}")
    print(f"\n  Sample document:")
    if docs:
        sample = docs[0]
        print(f"    text    : {sample['text'][:120]} …")
        print(f"    metadata: {sample['metadata']}")

    # ---- Step 2: Chunker --------------------------------------------------
    _step(2, "Chunking documents (size=500, overlap=50) …")
    chunks = chunk_documents(docs, chunk_size=500, overlap=50)
    print(f"  ✓ Produced {len(chunks)} chunks from {len(docs)} documents.")
    avg_len = sum(len(c["text"]) for c in chunks) / max(len(chunks), 1)
    print(f"  Average chunk length: {avg_len:.0f} characters.")

    # ---- Step 3: Embedder -------------------------------------------------
    _step(3, "Embedding a small sample of chunks …")
    embedder = LocalEmbedder()
    sample_texts = [c["text"] for c in chunks[:5]]
    sample_embeddings = embedder.embed_texts(sample_texts)
    print(f"  ✓ Embedded {len(sample_embeddings)} texts.")
    print(f"  Embedding dimension: {len(sample_embeddings[0])}.")
    print(f"  First 5 values of embedding[0]: "
          f"{[round(v, 4) for v in sample_embeddings[0][:5]]}")

    # ---- Step 4: VectorStore ----------------------------------------------
    _step(4, "Storing sample chunks in ChromaDB …")
    store = AirportVectorStore(
        collection_name="demo_collection",
        persist_dir=PERSIST_DIR,
    )
    store.clear()  # fresh start for demo

    all_texts = [c["text"] for c in chunks]
    all_metas = [c["metadata"] for c in chunks]
    print("  Embedding ALL chunks (this may take 30–60 s on CPU) …")
    all_embeddings = embedder.embed_texts(all_texts)
    store.add_documents(all_texts, all_embeddings, all_metas)
    print(f"  ✓ Stored {store.count()} chunks in ChromaDB at '{PERSIST_DIR}'.")

    # ---- Step 5: Retriever ------------------------------------------------
    _step(5, "Running retrieval queries …")
    retriever = AirportRetriever(embedder=embedder, vector_store=store)

    retrieval_queries = [
        "How do I reach Gate B12?",
        "Where can I eat near Terminal 2?",
    ]

    for rq in retrieval_queries:
        results = retriever.retrieve(rq, top_k=3)
        print(f"\n  Query: '{rq}'")
        for rank, res in enumerate(results, 1):
            print(f"    #{rank}  [score={res['score']:.3f}] "
                  f"[{res['metadata'].get('category','')} / "
                  f"{res['metadata'].get('id','')}]")
            print(f"         {res['text'][:100]} …")

    # ---- Step 6: Prompt Builder -------------------------------------------
    _step(6, "Building a prompt from retrieved chunks …")
    test_query = "Are there any offers at the duty-free shops?"
    results = retriever.retrieve(test_query, top_k=3)
    prompt = build_prompt(query=test_query, retrieved_chunks=results)
    print(f"\n  Assembled prompt (first 600 chars):\n")
    print("  " + "\n  ".join(prompt[:600].split("\n")))
    print("  …")


# ---------------------------------------------------------------------------
# Demo: full pipeline
# ---------------------------------------------------------------------------
def demo_pipeline() -> None:
    """Run the full AirportRAGPipeline with all test queries."""

    _section("FULL PIPELINE DEMO (with Ollama)")

    pipeline = AirportRAGPipeline(
        json_path=JSON_PATH,
        ollama_model=OLLAMA_MODEL,
        ollama_base_url=OLLAMA_URL,
        persist_dir=PERSIST_DIR,
    )

    if not pipeline.is_indexed():
        print("\n  Knowledge base not yet indexed — running load_and_index() …")
        pipeline.load_and_index()
    else:
        print(f"\n  ✓ Knowledge base already indexed "
              f"({pipeline._vector_store.count()} chunks). Skipping re-index.")

    test_queries = [
        "Where is Gate B12 and how do I get there?",
        "What food options are available near Terminal 2?",
        "Are there any offers at the duty-free shops?",
        "Is there a lounge in Terminal 1 and how do I access it?",
        "Where is the medical center in the airport?",
    ]

    for i, q in enumerate(test_queries, 1):
        print(f"\n  ── Query {i} of {len(test_queries)} ──────────────────────────")
        print(f"  Q: {q}")
        print("  A: ", end="", flush=True)
        try:
            answer = pipeline.query(q, top_k=5)
            print(answer)
        except ConnectionError as ce:
            print(f"\n  [Ollama unavailable — showing raw retrieved context instead]")
            print(f"  Error: {ce}\n")
            # Fallback: show what would have been sent to the LLM.
            try:
                chunks_raw = pipeline._retriever.retrieve(q, top_k=3)
                for rank, r in enumerate(chunks_raw, 1):
                    print(f"  Context #{rank} [{r['metadata'].get('category','')}]: "
                          f"{r['text'][:150]} …")
            except Exception:  # noqa: BLE001
                pass
        except Exception as e:  # noqa: BLE001
            print(f"[Unexpected error] {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "█" * 64)
    print("  AeroGuide — AI Airport Companion RAG Pipeline Demo")
    print("█" * 64)

    # Verify the JSON file exists before proceeding.
    if not os.path.exists(JSON_PATH):
        print(f"\n  ERROR: airport_data.json not found at '{JSON_PATH}'.")
        print("  Please ensure it exists alongside this script.")
        sys.exit(1)

    # Run component-level walkthrough.
    demo_components()

    # Run the end-to-end pipeline.
    demo_pipeline()

    print(f"\n\n{'█' * 64}")
    print("  Demo complete! ✅")
    print("█" * 64 + "\n")
