import io
import uuid
from typing import List, Dict, Any

import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mcp.types import TextContent

RAG_STORE: Dict[str, Dict[str, Any]] = {}


def extract_pdf_text(pdf_bytes: bytes) -> List[str]:
    """Extract text from each page of a PDF.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        A list of page-level text strings extracted from the PDF.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages: List[str] = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return pages


@mcp.tool()  # type: ignore
def ingest_pdf(pdf_bytes: bytes, name: str = "document") -> TextContent:
    """Ingest a PDF into an in-memory RAG store.

    The PDF is split by page, embedded using TF-IDF, and stored
    under a generated document ID.

    Args:
        pdf_bytes: Raw PDF file bytes.
        name: Optional human-readable name for the document.

    Returns:
        TextContent containing the generated document ID.
    """
    pages = extract_pdf_text(pdf_bytes)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=4096,
    )
    embeddings = vectorizer.fit_transform(pages)

    doc_id = str(uuid.uuid4())
    RAG_STORE[doc_id] = {
        "name": name,
        "pages": pages,
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
    pages: List[str] = store["pages"]

    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, embeddings)[0]

    top_indices = np.argsort(scores)[-3:][::-1]
    answer = "\n\n".join(
        pages[i] for i in top_indices if scores[i] > 0
    )

    return TextContent(
        type="text",
        text=answer or "No relevant content found.",
    )
