"""Local retrieval for Philippine-law context (a small, source-based RAG layer)."""

import json
import math
import re
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "rag_data" / "philippine_laws.json"

_WORDS = re.compile(r"[a-z0-9]+")
_FOREIGN_JURISDICTIONS = re.compile(
    r"\b(united states|u\.s\.a?\.?|\bus\b|usa|american|california|new york|uk|united kingdom|"
    r"england|canada|australia|japan|china|korean?|german[y]?|france|singapore|"
    r"malaysia|indonesia|india|federal law|foreign law)\b",
    re.IGNORECASE,
)


def _tokens(text):
    return _WORDS.findall(text.lower())


@lru_cache(maxsize=1024)
def _load_documents():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def chunk_text(text, title, source_url, chunk_size=900, overlap=150):
    """Create overlap chunks from an uploaded or local Philippine-law document."""
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append({
            "title": title,
            "category": "Uploaded Philippine law text",
            "jurisdiction": "Philippines",
            "text": " ".join(words[start:end]),
            "source_url": source_url,
            "official": False,
        })
        if end == len(words):
            break
        start = end - overlap
    return chunks


def search(query, top_k=5):
    """Return relevant Philippine-law chunks; refuse foreign-jurisdiction searches."""
    if _FOREIGN_JURISDICTIONS.search(query):
        return []

    documents = _load_documents()
    query_terms = _tokens(query)
    if not query_terms:
        return []

    corpus_terms = [_tokens(doc["title"] + " " + doc["category"] + " " + doc["text"])
                    for doc in documents]
    lengths = [len(tokens) for tokens in corpus_terms]
    average_length = sum(lengths) / max(len(lengths), 1)

    document_frequency = {}
    for tokens in corpus_terms:
        for term in set(tokens):
            document_frequency[term] = document_frequency.get(term, 0) + 1

    scores = []
    for index, tokens in enumerate(corpus_terms):
        frequencies = {}
        for term in tokens:
            frequencies[term] = frequencies.get(term, 0) + 1

        score = 0.0
        for term in set(query_terms):
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            df = document_frequency.get(term, 0)
            inverse_frequency = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
            normalized_frequency = frequency * 2.2 / (
                frequency + 1.2 * (1 - 0.75 + 0.75 * lengths[index] / average_length)
            )
            score += inverse_frequency * normalized_frequency
        if score:
            scores.append((score, documents[index]))

    scores.sort(key=lambda item: item[0], reverse=True)
    return [document for _, document in scores[:top_k] if not _FOREIGN_JURISDICTIONS.search(document['jurisdiction'])]


def build_context(query, top_k=5):
    """Format retrieved Philippine-law evidence for the model prompt."""
    matches = search(query, top_k)
    if not matches:
        return ""

    blocks = ["RETRIEVED PHILIPPINE LAW EVIDENCE — use only these sources to ground factual claims:"]
    for number, document in enumerate(matches, 1):
        blocks.append(
            f"[SOURCE {number}] {document['title']} | {document['category']} | "
            f"Jurisdiction: {document['jurisdiction']}\n"
            f"Official source: {document['source_url']}\n"
            f"Text: {document['text']}"
        )
    return "\n\n".join(blocks)
