"""
chunker.py
----------
Splits long text documents into overlapping character-level chunks.

Chunk parameters
----------------
chunk_size : int  (default 500)
    Maximum number of characters per chunk.
overlap : int  (default 50)
    Number of characters shared between consecutive chunks to preserve
    context at boundaries.
"""

from __future__ import annotations

from typing import Any


def chunk_documents(
    documents: list[dict[str, Any]],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """Split each document's text into overlapping character-level chunks.

    Parameters
    ----------
    documents : list[dict]
        Input documents, each with keys ``"text"`` (str) and
        ``"metadata"`` (dict).
    chunk_size : int
        Maximum number of characters per output chunk.  Documents shorter
        than *chunk_size* are returned as a single chunk.
    overlap : int
        Number of characters that adjacent chunks share.  Must be strictly
        less than *chunk_size*.

    Returns
    -------
    list[dict]
        Chunked documents.  Each element is ``{"text": str, "metadata":
        dict}``.  The original metadata is preserved and augmented with
        ``"chunk_index"`` and ``"chunk_total"`` keys.

    Raises
    ------
    ValueError
        If *overlap* >= *chunk_size*.
    """
    if overlap >= chunk_size:
        raise ValueError(
            f"overlap ({overlap}) must be strictly less than chunk_size ({chunk_size})."
        )

    chunked: list[dict[str, Any]] = []

    for doc in documents:
        text: str = doc.get("text", "")
        metadata: dict[str, Any] = dict(doc.get("metadata", {}))

        if not text:
            # Preserve empty documents as-is so nothing is silently lost.
            chunked.append({"text": text, "metadata": {**metadata, "chunk_index": 0, "chunk_total": 1}})
            continue

        # Collect start positions of every chunk.
        start_positions: list[int] = list(range(0, len(text), chunk_size - overlap))
        chunks: list[str] = []
        for start in start_positions:
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:  # skip chunks that are purely whitespace
                chunks.append(chunk_text)

        if not chunks:
            chunks = [text.strip()]

        total = len(chunks)
        for idx, chunk_text in enumerate(chunks):
            chunked.append({
                "text": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_index": idx,
                    "chunk_total": total,
                },
            })

    return chunked
