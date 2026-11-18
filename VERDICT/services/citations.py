"""Finds legal citations in Gemini's answers and links them to a search on Lawphil."""

import re
from urllib.parse import quote_plus

MAX_CITATIONS = 8

# Codes that an "Article N of the ..." citation can point to, with their usual names.
CODES = {
    "labor code": "Labor Code",
    "civil code": "Civil Code",
    "revised penal code": "Revised Penal Code",
    "family code": "Family Code",
    "constitution": "1987 Constitution",
    "1987 constitution": "1987 Constitution",
    "rules of court": "Rules of Court",
}

_CODE_NAMES = "|".join(sorted((re.escape(name) for name in CODES), key=len, reverse=True))

PATTERNS = [
    # G.R. No. 158693, G.R. Nos. 158693-94
    ("CASE", re.compile(r"G\.\s?R\.\s*Nos?\.\s*(\d[\d\-–, &and]*\d|\d)", re.IGNORECASE),
     lambda m: f"G.R. No. {_clean_number(m.group(1))}"),
    # Republic Act No. 9262, R.A. No. 9262, R.A. 9262, RA 9262
    ("LAW", re.compile(r"\b(?:Republic\s+Act|R\.\s?A\.|RA)\s*(?:No\.?\s*)?(\d{2,5})\b", re.IGNORECASE),
     lambda m: f"Republic Act No. {m.group(1)}"),
    # Presidential Decree No. 442, P.D. 442
    ("LAW", re.compile(r"\b(?:Presidential\s+Decree|P\.\s?D\.)\s*(?:No\.?\s*)?(\d{1,4})\b", re.IGNORECASE),
     lambda m: f"Presidential Decree No. {m.group(1)}"),
    # Batas Pambansa Blg. 22, B.P. 22
    ("LAW", re.compile(r"\b(?:Batas\s+Pambansa|B\.\s?P\.)\s*(?:Blg\.?|Bilang|No\.?)?\s*(\d{1,4})\b", re.IGNORECASE),
     lambda m: f"Batas Pambansa Blg. {m.group(1)}"),
    # Article 294 of the Labor Code, Art. 297 of the Civil Code, Article 294
    ("LAW", re.compile(
        r"\b(?:Article|Art\.)\s*(\d{1,4}[A-Z]?)\b"
        rf"(?:\s*(?:,|of)\s*(?:the\s+)?({_CODE_NAMES}))?",
        re.IGNORECASE),
     lambda m: _article_label(m.group(1), m.group(2))),
]


def _clean_number(text):
    """Tidy a G.R. number: keep digits and dashes, drop trailing joiners."""
    first = re.split(r"[,&]|\band\b", text)[0]
    return first.replace("–", "-").strip(" -")


def _article_label(number, code):
    if code:
        return f"Article {number.upper()}, {CODES[code.lower()]}"
    return f"Article {number.upper()}"


def search_url(label):
    """A Google search limited to Lawphil, which hosts Philippine laws and decisions."""
    return "https://www.google.com/search?q=" + quote_plus(f'site:lawphil.net "{label}"')


def extract_citations(text):
    """Return up to MAX_CITATIONS citations, in the order they appear in the text.

    Each citation is a dict: {"kind": "CASE" or "LAW", "label": str, "url": str}.
    """
    found = []
    for kind, pattern, make_label in PATTERNS:
        for match in pattern.finditer(text):
            found.append((match.start(), kind, make_label(match)))
    found.sort(key=lambda item: item[0])

    citations, seen = [], set()
    for _, kind, label in found:
        if label in seen:
            continue
        # "Article 294" adds nothing when "Article 294, Labor Code" is already listed.
        if any(existing.startswith(label + ",") for existing in seen):
            continue
        seen.add(label)
        citations.append({"kind": kind, "label": label, "url": search_url(label)})

    # Drop a bare "Article N" when a fuller version of it appears later.
    labels = {c["label"] for c in citations}
    citations = [
        c for c in citations
        if not any(other.startswith(c["label"] + ",") for other in labels)
    ]
    return citations[:MAX_CITATIONS]