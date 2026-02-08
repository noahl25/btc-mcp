import uuid
from typing import List, Dict, Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mcp.types import TextContent

RAG_STORE: Dict[str, Dict[str, Any]] = {}


@mcp.tool()  # type: ignore
def ingest_text(text: str, name: str = "document") -> TextContent:
    """Ingest plain text into an in-memory RAG store.

    The text is split into chunks by double newlines, embedded using TF-IDF,
    and stored under a generated document ID.

    Args:
        text: The plain text content to ingest.
        name: Optional human-readable name for the document.

    Returns:
        TextContent containing the generated document ID.
    """
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if not chunks:
        return TextContent(type="text", text="No content to ingest.")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=4096,
    )
    embeddings = vectorizer.fit_transform(chunks)

    doc_id = str(uuid.uuid4())
    RAG_STORE[doc_id] = {
        "name": name,
        "chunks": chunks,
        "vectorizer": vectorizer,
        "embeddings": embeddings,
    }

    return TextContent(
        type="text",
        text=f"PDF ingested with ID: {doc_id}",
    )


@mcp.tool()  # type: ignore
def query_rag(doc_id: str, query: str) -> TextContent:
    """Query a previously ingested PDF using similarity search.

    Performs cosine similarity between the query and stored
    TF-IDF page embeddings, returning the top matches.

    Args:
        doc_id: ID of the ingested PDF to query.
        query: Natural language search query.

    Returns:
        TextContent containing the most relevant page text.
    """
    store = RAG_STORE.get(doc_id)
    if not store:
        return TextContent(
            type="text",
            text="Invalid document ID.",
        )

    vectorizer: TfidfVectorizer = store["vectorizer"]
    embeddings = store["embeddings"]
    chunks: List[str] = store["chunks"]

    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, embeddings)[0]

    top_indices = np.argsort(scores)[-3:][::-1]
    answer = "\n\n".join(
        chunks[i] for i in top_indices if scores[i] > 0
    )

    return TextContent(
        type="text",
        text=answer or "No relevant content found.",
    )
