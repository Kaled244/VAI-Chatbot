"""Builds a downloadable record of the conversation as a Word file or plain text."""

import io
import re
from datetime import datetime

from docx import Document as WordFile
from docx.shared import Pt, RGBColor

TITLE = "VERDICT — Case Record"
DISCLAIMER = (
    "This record contains legal information, not legal advice. VERDICT is not a lawyer. "
    "Bring this to a licensed Philippine lawyer for advice on your situation."
)
BURGUNDY = RGBColor(0x6B, 0x1D, 0x2A)


def exportable_messages(messages):
    """The messages worth keeping: real questions and answers, no error notices."""
    return [m for m in messages if not m.get("error")]


def file_name(extension):
    return f"verdict-record-{datetime.now():%Y%m%d-%H%M}.{extension}"


def _speaker(message):
    return "You" if message["role"] == "user" else "VERDICT"


def _attached_document(message):
    """The name of a document sent with a message, if any."""
    match = re.search(r"\[ATTACHED DOCUMENT: ([^\]\(]+?)\s*(?:\(|\])", message.get("context", ""))
    return match.group(1) if match else ""


# ---------- Plain text ----------

def _plain(text):
    """Remove Markdown symbols (**bold**, # headings, ---) so the text reads cleanly."""
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)\*([^*\s][^*]*)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^\s*#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_text(messages, mode, citations):
    """The record as plain text, readable in any app."""
    lines = [
        TITLE,
        f"Date: {datetime.now():%B %d, %Y %I:%M %p}",
        f"Mode: {mode}",
        "",
        DISCLAIMER,
        "",
        "=" * 60,
    ]
    for message in exportable_messages(messages):
        lines += ["", f"{_speaker(message)}:"]
        document = _attached_document(message)
        if document:
            lines.append(f"[Attached document: {document}]")
        lines.append(_plain(message["content"]))

    if citations:
        lines += ["", "=" * 60, "", "Citations from the latest answer:"]
        lines += [f"- {c['label']}" for c in citations]
    return "\n".join(lines) + "\n"


# ---------- Word ----------

_INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)")


def _add_inline(paragraph, text):
    """Add text to a Word paragraph, turning **bold**, *italic* and `code` into formatting."""
    for piece in _INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**"):
            paragraph.add_run(piece[2:-2]).bold = True
        elif piece.startswith("`") and piece.endswith("`"):
            paragraph.add_run(piece[1:-1])
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            paragraph.add_run(piece[1:-1]).italic = True
        else:
            paragraph.add_run(piece)


def _add_markdown(document, text):
    """Write Gemini's Markdown answer into the Word document with matching structure."""
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if not stripped or re.fullmatch(r"[-*_]{3,}", stripped):
            continue
        heading = re.match(r"(#{1,6})\s+(.*)", stripped)
        bullet = re.match(r"[-*+]\s+(.*)", stripped)
        numbered = re.match(r"\d+[.)]\s+(.*)", stripped)

        if heading:
            level = min(len(heading.group(1)) + 1, 4)
            _add_inline(document.add_heading(level=level), heading.group(2))
        elif bullet:
            style = "List Bullet 2" if indent >= 2 else "List Bullet"
            _add_inline(document.add_paragraph(style=style), bullet.group(1))
        elif numbered:
            style = "List Number 2" if indent >= 2 else "List Number"
            _add_inline(document.add_paragraph(style=style), numbered.group(1))
        else:
            _add_inline(document.add_paragraph(), stripped)


def build_docx(messages, mode, citations):
    """The record as a Word file. Returns the file's bytes."""
    document = WordFile()
    document.styles["Normal"].font.name = "Calibri"
    document.styles["Normal"].font.size = Pt(11)

    document.add_heading(TITLE, level=0)
    info = document.add_paragraph()
    info.add_run(f"Date: {datetime.now():%B %d, %Y %I:%M %p}\nMode: {mode}")
    note = document.add_paragraph()
    note_run = note.add_run(DISCLAIMER)
    note_run.italic = True
    note_run.font.size = Pt(9)

    for message in exportable_messages(messages):
        speaker = document.add_paragraph()
        speaker_run = speaker.add_run(_speaker(message))
        speaker_run.bold = True
        speaker_run.font.color.rgb = BURGUNDY
        speaker.paragraph_format.space_before = Pt(14)

        attached = _attached_document(message)
        if attached:
            document.add_paragraph().add_run(f"Attached document: {attached}").italic = True

        if message["role"] == "user":
            document.add_paragraph(message["content"].strip())
        else:
            _add_markdown(document, message["content"])

    if citations:
        document.add_heading("Citations from the latest answer", level=2)
        for citation in citations:
            document.add_paragraph(citation["label"], style="List Bullet")

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()