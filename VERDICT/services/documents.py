"""Reads uploaded documents (PDF, Word, text) into plain text for the model."""

import io
from dataclasses import dataclass

import streamlit as st
from docx import Document as WordFile
from pypdf import PdfReader

SUPPORTED_TYPES = ["pdf", "docx", "txt"]
MAX_DOCUMENT_CHARS = 10000  # longer documents are cut to this length


@dataclass
class Document:
    """The result of reading one uploaded file."""
    name: str
    text: str = ""          # the text sent to the model (possibly shortened)
    total_chars: int = 0    # length of the full text found in the file
    truncated: bool = False
    error: str = ""         # set when the file could not be read


def _read_pdf(data):
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        reader.decrypt("")  # works only for PDFs without a real password
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _read_docx(data):
    file = WordFile(io.BytesIO(data))
    lines = [paragraph.text for paragraph in file.paragraphs]
    for table in file.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(lines)


def _read_txt(data):
    return data.decode("utf-8", errors="ignore")


READERS = {"pdf": _read_pdf, "docx": _read_docx, "txt": _read_txt}


@st.cache_data(show_spinner=False)
def _extract(name, data):
    """Read the file once; Streamlit reuses the result on later reruns."""
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    reader = READERS.get(extension)
    if reader is None:
        return Document(name=name, error="Unsupported file type. Upload a PDF, Word (.docx), or .txt file.")

    try:
        text = reader(data).strip()
    except Exception:
        return Document(name=name, error="This file could not be read. It may be damaged or password-protected.")

    if not text:
        if extension == "pdf":
            return Document(name=name, error="No text found in this PDF. It may be a scanned image; upload a text-based PDF instead.")
        return Document(name=name, error="This file is empty.")

    return Document(
        name=name,
        text=text[:MAX_DOCUMENT_CHARS],
        total_chars=len(text),
        truncated=len(text) > MAX_DOCUMENT_CHARS,
    )


def read_document(uploaded):
    """Turn a Streamlit uploaded file into a Document. Returns None when nothing is uploaded."""
    if uploaded is None:
        return None
    return _extract(uploaded.name, uploaded.getvalue())