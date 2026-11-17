import os
import time
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompts.verdict import VERDICT_SYSTEM_PROMPT

load_dotenv()

st.set_page_config(
    page_title="VERDICT — Your AI Legal Guide",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# THEME
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');
    :root {
        --burgundy: #6B1D2A; --navy: #1B2A41; --gold: #C9A227;
        --ivory: #FAF7F0; --ink: #2B2B2B; --muted: #6E6A63;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif; color: var(--ink); background-color: var(--ivory);
    }
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif !important; color: var(--navy) !important;
        letter-spacing: 0.3px;
    }
    .verdict-title {
        font-family: 'Playfair Display', serif; font-size: 2.6rem; font-weight: 700;
        color: var(--navy); margin: 0; line-height: 1.1; letter-spacing: 1px;
    }
    .verdict-subtitle {
        font-family: 'Inter', sans-serif; font-size: 1rem; color: var(--muted);
        margin-top: 4px; letter-spacing: 2px; text-transform: uppercase;
    }
    [data-testid="stChatMessage"] p, [data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem; line-height: 1.7;
    }
    .stButton > button {
        border-radius: 8px; border: 1.5px solid var(--burgundy); background-color: #FFFFFF;
        color: var(--burgundy); font-weight: 600; font-size: 0.95rem;
        padding: 0.55rem 1rem; transition: all 0.18s ease;
    }
    .stButton > button:hover {
        background-color: var(--burgundy); color: #FFFFFF; border-color: var(--burgundy);
    }
    .stButton > button[kind="primary"] {
        background-color: var(--burgundy); color: #FFFFFF; border: 1.5px solid var(--burgundy);
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--navy); border-color: var(--navy);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; border: 1px solid #E8E2D2 !important;
        border-radius: 12px !important; box-shadow: 0 2px 6px rgba(27, 42, 65, 0.04);
    }
    hr { border: none; border-top: 1px solid var(--gold); opacity: 0.5; }
    [data-testid="stChatInput"] textarea { font-size: 1rem; }
    [data-testid="stChatInput"] { border-top: 2px solid var(--gold); padding-top: 8px; }
    .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; font-size: 0.82rem; }
    .nav-label {
        font-family: 'Playfair Display', serif; font-size: 1.15rem; color: var(--navy);
        font-weight: 600; margin-bottom: 6px;
    }
    .section-label {
        font-family: 'Inter', sans-serif; font-size: 0.78rem; letter-spacing: 1.5px;
        text-transform: uppercase; color: var(--burgundy); font-weight: 600;
        margin: 12px 0 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# GEMINI CLIENT
# ==========================================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found. Please add it to your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.8-flash"

# ==========================================
# SESSION STATE INIT
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "Legal Chat"
if "category" not in st.session_state:
    st.session_state.category = "Labor / Civil / Criminal"
if "last_references" not in st.session_state:
    st.session_state.last_references = []

# ==========================================
# HELPERS
# ==========================================
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

def build_system_prompt():
    """Assemble system prompt from base + active mode + selected categories."""
    base = VERDICT_SYSTEM_PROMPT
    mode = st.session_state.mode
    mode_instruction = MODE_PROMPTS.get(mode, MODE_PROMPTS["Legal Chat"])

    categories = []
    if st.session_state.get("cat_civil"):    categories.append("Civil / Housing")
    if st.session_state.get("cat_labor"):    categories.append("Labor / Employment")
    if st.session_state.get("cat_criminal"): categories.append("Criminal Law")
    if st.session_state.get("cat_family"):   categories.append("Personal / Family")

    parts = [base, f"\n\nACTIVE MODE — {mode}: {mode_instruction}"]
    if categories:
        parts.append(f"\nFocus areas: {', '.join(categories)}.")
    return "\n".join(parts)

def call_gemini(user_prompt, extra_context=""):
    """Send a prompt to Gemini with retry logic. Returns reply text."""
    full_prompt = user_prompt
    if extra_context:
        full_prompt = f"{extra_context}\n\n---\n\n{user_prompt}"

    system_instruction = build_system_prompt()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=full_prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction),
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    return "The servers are overwhelmed. I cannot give you an answer right now. Try again shortly."
            else:
                return f"⚠️ Error: `{error_msg}`"
    return "⚠️ Unknown error."

def extract_references(reply_text):
    """Naive extraction of statute/case mentions to populate the References card."""
    import re
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

# ==========================================
# HEADER
# ==========================================
col_logo, col_title, col_btn1, col_btn2 = st.columns([0.6, 5, 1, 1])
with col_logo:
    st.markdown("<div style='font-size:2.6rem; line-height:1;'>⚖️</div>", unsafe_allow_html=True)
with col_title:
    st.markdown(
        "<div class='verdict-title'>VERDICT</div>"
        "<div class='verdict-subtitle'>\"I keep my eyes open.\"</div>",
        unsafe_allow_html=True,
    )
with col_btn1:
    if st.button("Clear the Record", use_container_width=True, key="header_clear"):
        st.session_state.messages = []
        st.session_state.last_references = []
        st.rerun()
with col_btn2:
    if st.button("Settings", use_container_width=True, key="header_settings"):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)

if st.session_state.get("show_settings"):
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Settings</div>", unsafe_allow_html=True)
        st.caption(f"Model: `{MODEL_NAME}`")
        new_model = st.text_input("Model name", value=MODEL_NAME, key="settings_model")
        if new_model != MODEL_NAME:
            MODEL_NAME = new_model
        st.caption("Session state is cleared on Clear the Record.")

st.markdown("<hr/>", unsafe_allow_html=True)

# ==========================================
# MAIN LAYOUT
# ==========================================
col_left, col_mid, col_right = st.columns([1.4, 4, 2.4], gap="large")

# ---------- LEFT: Navigation & Filters ----------
with col_left:
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Proceedings</div>", unsafe_allow_html=True)
        for mode in MODE_PROMPTS:
            is_active = st.session_state.mode == mode
            if st.button(
                MODE_LABELS.get(mode, mode),
                use_container_width=True,
                type="primary" if is_active else "secondary",
                key=f"nav_{mode.replace(' ', '_').lower()}",
            ):
                st.session_state.mode = mode
                st.rerun()

        st.markdown("<div class='section-label'>Jurisdiction</div>", unsafe_allow_html=True)
        st.checkbox("Civil / Housing", value=True, key="cat_civil")
        st.checkbox("Labor / Employment", value=True, key="cat_labor")
        st.checkbox("Criminal Law", value=True, key="cat_criminal")
        st.checkbox("Personal / Family", value=True, key="cat_family")

        st.markdown("<div class='section-label'>Sources</div>", unsafe_allow_html=True)
        st.caption("Lawphil · Supreme Court E-Library · Official Gazette")

    st.caption(
        "I provide legal information, not legal advice. I am not your attorney. "
        "For matters that carry real weight, retain a licensed Philippine lawyer."
    )

# ---------- MIDDLE: Chat ----------
with col_mid:
    with st.container(border=True):
        st.markdown("<div class='section-label'>Counsel suggests</div>", unsafe_allow_html=True)
        sq1, sq2, sq3 = st.columns(3)
        with sq1:
            if st.button("I was fired without notice.", use_container_width=True, key="sq_terminated"):
                st.session_state.messages.append({"role": "user", "content": "I was terminated without notice. What are my rights?"})
                st.rerun()
        with sq2:
            if st.button("My landlord kept my deposit.", use_container_width=True, key="sq_deposit"):
                st.session_state.messages.append({"role": "user", "content": "My landlord refuses to return my security deposit. What are my options?"})
                st.rerun()
        with sq3:
            if st.button("I was arrested. What now?", use_container_width=True, key="sq_arrested"):
                st.session_state.messages.append({"role": "user", "content": "I was arrested. What are my rights?"})
                st.rerun()

    chat_container = st.container(height=520, border=True)
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                "<div style='text-align:center; padding:2rem 0; color:#6E6A63;'>"
                "<div style='font-size:2.2rem;'>🔨</div>"
                "<div style='font-family:Playfair Display, serif; font-size:1.4rem; color:#1B2A41; margin-top:8px;'>"
                "The court is in session.</div>"
                "<div style='font-size:0.95rem; margin-top:6px;'>State your case.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        for msg in st.session_state.messages:
            avatar = "🔨" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    if prompt := st.chat_input("State the facts. Leave nothing out."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# ---------- RIGHT: Situation & References ----------
with col_right:
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Case File</div>", unsafe_allow_html=True)
        st.selectbox(
            "Category",
            ["Labor / Civil / Criminal", "Civil / Housing", "Labor / Employment", "Criminal Law", "Personal / Family"],
            key="right_category",
        )
        facts = st.text_area(
            "Facts of the situation",
            height=110,
            placeholder="Describe what happened. In order. Without omitting anything.",
            key="right_facts",
        )
        st.checkbox("Show both sides' arguments", key="right_both_sides")
        uploaded = st.file_uploader("Attach document (optional)", label_visibility="collapsed", key="right_upload")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Analyze", use_container_width=True, type="primary", key="right_analyze"):
                if not facts.strip():
                    st.warning("You have given me nothing to work with. State the facts first.")
                else:
                    st.session_state.mode = "Situation Analysis"
                    context = f"[CATEGORY: {st.session_state.right_category}]"
                    if st.session_state.right_both_sides:
                        context += " [PRESENT BOTH SIDES]"
                    if uploaded is not None:
                        try:
                            doc_text = uploaded.read().decode("utf-8", errors="ignore")[:5000]
                            context += f"\n\n[ATTACHED DOCUMENT]\n{doc_text}"
                        except Exception:
                            context += "\n\n[ATTACHED DOCUMENT: could not read]"
                    st.session_state.messages.append({"role": "user", "content": facts})
                    st.session_state.pending_context = context
                    st.rerun()
        with btn_col2:
            if st.button("Lawyer Prep", use_container_width=True, key="right_lawyer_prep"):
                if not facts.strip():
                    st.warning("I cannot prepare a case from silence. Give me the facts.")
                else:
                    st.session_state.mode = "Lawyer Prep"
                    st.session_state.messages.append({"role": "user", "content": facts})
                    st.session_state.pending_context = "Prepare this client for a lawyer meeting."
                    st.rerun()

    with st.container(border=True):
        st.markdown("<div class='nav-label'>Citations</div>", unsafe_allow_html=True)
        if st.session_state.last_references:
            for kind, val in st.session_state.last_references:
                icon = "⚖️" if kind == "CASE" else "📜"
                st.markdown(f"{icon} **{kind}**")
                st.caption(val)
                st.markdown("<hr/>", unsafe_allow_html=True)
        else:
            st.caption("Citations from the latest exchange will appear here.")

# ==========================================
# GENERATION — append reply, then rerun so the history renders it
# ==========================================
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    context = st.session_state.pop("pending_context", "")

    with col_mid:
        with st.spinner("Reviewing the facts..."):
            reply = call_gemini(last_user_msg, extra_context=context)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_references = extract_references(reply)
    st.rerun()