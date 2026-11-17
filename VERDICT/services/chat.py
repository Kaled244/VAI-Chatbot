"""Chat logic: session state, modes, prompt assembly, and reply handling.

Nothing in this file draws UI. The ui/ folder calls these functions.
"""

import re

import streamlit as st

from ai.client import DEFAULT_MODEL, GeminiError, generate_reply
from ai.prompts.verdict import VERDICT_SYSTEM_PROMPT

MODE_PROMPTS = {
    "Legal Chat":        "Respond conversationally to the user's legal question.",
    "Situation Analysis":"Analyze the user's situation step-by-step. Identify the legal issue, applicable laws, and likely outcomes.",
    "Law Search":        "Identify and cite specific Philippine statutes, articles, and jurisprudence relevant to the query. Include G.R. numbers when possible.",
    "Know Your Rights":  "Explain the user's rights clearly and concisely, citing the constitutional or statutory basis for each.",
    "Document Guide":    "Guide the user on what legal document or form they need, what fields it requires, and where to file it.",
    "Debate Analysis":   "Present both sides of the legal issue — arguments for and against — then give a balanced conclusion.",
    "Lawyer Prep":       "Prepare the user for a meeting with a lawyer: summarize their situation, list key facts, and suggest questions to ask.",
}

MODE_LABELS = {
    "Legal Chat":        "Consultation",
    "Situation Analysis":"Examine the Facts",
    "Law Search":        "Find the Precedent",
    "Know Your Rights":  "Know Your Rights",
    "Document Guide":    "Draft the Paperwork",
    "Debate Analysis":   "Hear Both Sides",
    "Lawyer Prep":       "Prepare for Court",
}

CATEGORY_OPTIONS = [
    "Labor / Civil / Criminal",
    "Civil / Housing",
    "Labor / Employment",
    "Criminal Law",
    "Personal / Family",
]

MAX_HISTORY_MESSAGES = 20  # how many past messages Gemini sees


# ---------- Session state ----------

def init_session_state():
    """Set default values the first time the app loads in a session."""
    defaults = {
        "messages": [],
        "mode": "Legal Chat",
        "last_references": [],
        "model_name": DEFAULT_MODEL,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_user_message(content, context=""):
    """Add a user message to the history, with optional hidden context for the model.

    The context (category, attached document) is stored with the message so
    Gemini still sees it in later follow-up questions. It is never displayed.
    """
    message = {"role": "user", "content": content}
    if context:
        message["context"] = context
    st.session_state.messages.append(message)


def clear_conversation():
    """Wipe the chat history and the citations."""
    st.session_state.messages = []
    st.session_state.last_references = []


# ---------- Prompt assembly ----------

def build_system_prompt():
    """Assemble system prompt from base + active mode + selected categories."""
    mode = st.session_state.mode
    mode_instruction = MODE_PROMPTS.get(mode, MODE_PROMPTS["Legal Chat"])

    categories = []
    if st.session_state.get("cat_civil"):    categories.append("Civil / Housing")
    if st.session_state.get("cat_labor"):    categories.append("Labor / Employment")
    if st.session_state.get("cat_criminal"): categories.append("Criminal Law")
    if st.session_state.get("cat_family"):   categories.append("Personal / Family")

    parts = [VERDICT_SYSTEM_PROMPT, f"\n\nACTIVE MODE — {mode}: {mode_instruction}"]
    if categories:
        parts.append(f"\nFocus areas: {', '.join(categories)}.")
    return "\n".join(parts)


def document_context(document):
    """Hidden text that gives the model the attached document, if one was read."""
    if document is None or not document.text:
        return ""
    note = " (beginning only, the document was too long)" if document.truncated else ""
    return f"\n\n[ATTACHED DOCUMENT: {document.name}{note}]\n{document.text}"


def build_analysis_context(category, both_sides=False, document=None):
    """Build the hidden context sent with a Case File analysis."""
    context = f"[CATEGORY: {category}]"
    if both_sides:
        context += " [PRESENT BOTH SIDES]"
    return context + document_context(document)


def build_lawyer_prep_context(document=None):
    """Build the hidden context sent with a Lawyer Prep request."""
    return "Prepare this client for a lawyer meeting." + document_context(document)


# ---------- Replies ----------

def needs_reply():
    """True when the last message is from the user and is still unanswered."""
    messages = st.session_state.messages
    return bool(messages) and messages[-1]["role"] == "user"


def conversation_history():
    """The recent messages Gemini should see: no error notices, starting with a user turn."""
    history = [m for m in st.session_state.messages if not m.get("error")]
    history = history[-MAX_HISTORY_MESSAGES:]
    while history and history[0]["role"] != "user":
        history.pop(0)
    return history


def answer_last_message():
    """Ask Gemini to answer the latest user message, using the conversation so far."""
    try:
        reply = generate_reply(
            messages=conversation_history(),
            system_instruction=build_system_prompt(),
            model=st.session_state.model_name,
        )
    except GeminiError as error:
        # Shown in the chat, but flagged so it is never sent back to Gemini as history.
        st.session_state.messages.append(
            {"role": "assistant", "content": f"⚠️ {error}", "error": True}
        )
        return

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_references = extract_references(reply)


def extract_references(reply_text):
    """Naive extraction of statute/case mentions to populate the Citations card."""
    refs = []
    for m in re.findall(r"G\.R\.\s*No\.\s*[\d\-]+", reply_text):
        refs.append(("CASE", m))
    for m in re.findall(r"(Republic Act No\.\s*\d+|Article \d+[A-Z]?)", reply_text):
        refs.append(("LAW", m))
    seen, unique = set(), []
    for kind, val in refs:
        if val not in seen:
            seen.add(val)
            unique.append((kind, val))
    return unique[:5]