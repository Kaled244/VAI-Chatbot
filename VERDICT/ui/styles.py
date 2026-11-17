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
</style>
"""


def apply_theme():
    """Inject the VERDICT theme into the page."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)