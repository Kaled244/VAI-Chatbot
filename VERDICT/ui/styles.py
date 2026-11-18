"""Visual theme for VERDICT: fonts, colors, and custom CSS."""

import streamlit as st

THEME_CSS = """
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

    /* ---------- Fixes ---------- */

    /* Keep the page fully visible while an answer is being written
       (Streamlit normally fades everything during a rerun). */
    [data-stale="true"] { opacity: 1 !important; transition: none !important; }

    /* Let button labels wrap onto a second line instead of being cut off with "...". */
    .stButton > button { height: auto; min-height: 2.6rem; }
    .stButton > button * {
        white-space: normal !important; overflow: visible !important;
        text-overflow: clip !important; line-height: 1.3;
    }
    /* Suggested questions: same height even when one label wraps. */
    [class*="st-key-sq_"] button { min-height: 3.4rem; }

    /* Never split a word in half; long labels wrap between words. */
    .stButton > button *, .nav-label, .section-label, [data-testid="stCheckbox"] * {
        word-break: normal !important; overflow-wrap: normal !important;
    }

    /* Smaller buttons when the window is narrow (laptops, split screen). */
    @media (max-width: 1250px) {
        .stButton > button { padding: 0.45rem 0.5rem; font-size: 0.86rem; }
        .nav-label { font-size: 1.02rem; }
        .section-label { letter-spacing: 0.8px; }
        [data-testid="stCheckbox"] p { font-size: 0.88rem; }
    }

    /* Less empty space above the header. */
    [data-testid="stMainBlockContainer"] { padding-top: 4rem; }

    /* Headings inside answers: sized for a chat bubble, not a page title. */
    [data-testid="stChatMessage"] h1 { font-size: 1.3rem !important; }
    [data-testid="stChatMessage"] h2 { font-size: 1.2rem !important; }
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4 { font-size: 1.1rem !important; }
    [data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3, [data-testid="stChatMessage"] h4 {
        margin: 0.8rem 0 0.3rem 0 !important; padding: 0 !important;
    }

    /* Hide Streamlit's own Deploy button, menu and footer. */
    [data-testid="stAppDeployButton"], #MainMenu, footer { display: none !important; }

    /* ---------- Active mode banner ---------- */
    .mode-banner {
        display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px;
        padding: 2px 0 10px 0; margin-bottom: 6px; border-bottom: 1px solid #F0EBDD;
    }
    .mode-tag {
        font-family: 'Inter', sans-serif; font-size: 0.7rem; letter-spacing: 1.5px;
        text-transform: uppercase; color: var(--muted); font-weight: 600;
    }
    .mode-name {
        font-family: 'Playfair Display', serif; font-size: 1.1rem; color: var(--burgundy); font-weight: 700;
    }
    .mode-desc { font-size: 0.88rem; color: var(--muted); }

    /* ---------- Compact citations ---------- */
    .cite-list { margin: 2px 0 6px 0; }
    .cite {
        display: flex; align-items: baseline; gap: 8px;
        padding: 7px 0; border-bottom: 1px solid #F0EBDD; font-size: 0.92rem;
    }
    .cite:last-child { border-bottom: none; }
    .cite-kind {
        flex-shrink: 0; font-size: 0.66rem; letter-spacing: 1px; font-weight: 700;
        border-radius: 4px; padding: 2px 6px;
    }
    .cite-kind.case { color: var(--burgundy); background: #F6EDEF; }
    .cite-kind.law  { color: var(--navy); background: #ECEFF4; }
    .cite a { color: var(--ink); text-decoration: none; border-bottom: 1px dotted var(--gold); }
    .cite a:hover { color: var(--burgundy); border-bottom-color: var(--burgundy); }
</style>
"""


def apply_theme():
    """Inject the VERDICT theme into the page."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)