"""
prompt_builder.py
-----------------
Assembles the final LLM prompt from retrieved context chunks and the
user's question, using the AeroGuide system persona.

The prompt template instructs the model to:
  - Act as AeroGuide, a friendly airport AI companion.
  - Answer ONLY from the provided context.
  - Gracefully decline when the context does not contain the answer.
"""

from __future__ import annotations

_SYSTEM_PERSONA = (
    "You are AeroGuide, an AI Airport Companion. "
    "You help travelers with navigation, gate directions, food, shopping, "
    "offers, facilities, and services inside the airport. "
    "Use ONLY the context provided below to answer. "
    "Be concise, friendly, and helpful. "
    "If the answer is not found in the context, say "
    '"I don\'t have that information right now, please check the airport information desk."'
)

_SEPARATOR = "\n---\n"


def build_prompt(query: str, retrieved_chunks: list[dict]) -> str:
    """Build the full LLM prompt from a query and retrieved context chunks.

    Parameters
    ----------
    query : str
        The raw question submitted by the airport passenger.
    retrieved_chunks : list[dict]
        Output from :meth:`~retriever.AirportRetriever.retrieve`.  Each
        element must have at least a ``"text"`` key.  Additional keys
        (``"metadata"``, ``"score"``) are silently ignored.

    Returns
    -------
    str
        A fully-formatted prompt string ready to be sent to an LLM.

    Notes
    -----
    If *retrieved_chunks* is empty the context section will contain a
    fallback notice rather than being blank, so the model still receives a
    well-formed prompt.
    """
    if retrieved_chunks:
        context_text = _SEPARATOR.join(
            chunk["text"] for chunk in retrieved_chunks if chunk.get("text")
        )
    else:
        context_text = "(No relevant context was found for this query.)"

    prompt = (
        f"{_SYSTEM_PERSONA}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Passenger Question: {query}\n\n"
        f"AeroGuide Answer:"
    )
    return prompt
