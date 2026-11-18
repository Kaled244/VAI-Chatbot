"""VERDICT entry point. Run with: streamlit run app.py

This file only wires the parts together:
    ui/        what the user sees
    services/  chat logic and session state
    ai/        Gemini client and prompts
"""

import streamlit as st

from ai.client import has_api_key
from services import chat
from ui import components
from ui.styles import apply_theme

st.set_page_config(
    page_title="VERDICT — Your AI Legal Guide",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()

if not has_api_key():
    st.error("⚠️ GEMINI_API_KEY not found. Please add it to your .env file.")
    st.stop()

chat.init_session_state()

components.render_header()

col_left, col_mid, col_right = st.columns([1.6, 4, 2.4], gap="large")

with col_left:
    components.render_navigation()

with col_mid:
    chat_history = components.render_chat()

with col_right:
    components.render_case_file()
    components.render_citations()
    components.render_export()

# Stream a reply when the last message is from the user,
# then rerun so the history shows it.
if chat.needs_reply():
    components.render_streaming_reply(chat_history)
    st.rerun()