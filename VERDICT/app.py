import os
import time
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompts.verdict import VERDICT_SYSTEM_PROMPT

# Load environment variables from .env
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found. Please add it to your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.8-flash"

# Page config - Set to wide to fit the 3 columns
st.set_page_config(page_title="VERDICT - Your AI Legal Guide", page_icon="⚖️", layout="wide")

# --- TOP HEADER ---
col_logo, col_title, col_btn1, col_btn2, col_btn3 = st.columns([1, 4, 1, 1, 1])
with col_logo:
    st.title("⚖️")
with col_title:
    st.markdown("<h2 style='margin-top: 15px;'>VERDICT</h2>", unsafe_allow_html=True)
with col_btn1:
    st.button("New Chat", use_container_width=True)
with col_btn2:
    if st.button("Clear", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
with col_btn3:
    st.button("Settings", use_container_width=True)

st.divider()

# --- MAIN LAYOUT (3 Columns) ---
col_left, col_mid, col_right = st.columns([1.5, 4, 2.5], gap="large")

# ==========================================
# LEFT SIDEBAR (Navigation & Filters)
# ==========================================
with col_left:
    with st.container(border=True):
        st.button("Legal Chat", use_container_width=True, type="primary")
        st.button("Situation Analysis", use_container_width=True)
        st.button("Law Search", use_container_width=True)
        st.button("Know Your Rights", use_container_width=True)
        st.button("Document Guide", use_container_width=True)
        st.button("Debate Analysis", use_container_width=True)
        st.button("Lawyer Prep", use_container_width=True)
        
        st.write("**Categories**")
        st.checkbox("Civil / Housing", value=True)
        st.checkbox("Labor / Employment", value=True)
        st.checkbox("Criminal Law", value=True)
        st.checkbox("Personal / Family", value=True)
        
        st.divider()
        st.write("**Sources:**")
        st.caption("Lawphil, Supreme Court E-Library, Official Gazette")
        
    st.caption("⚠️ *VERDICT provides general legal information only. It does not constitute legal advice. Consult a licensed Philippine lawyer for your specific situation.*")

# ==========================================
# MIDDLE COLUMN (Main Chat Interface)
# ==========================================
with col_mid:
    # Suggested Questions
    with st.container(border=True):
        st.markdown("**Suggested questions**")
        sq1, sq2, sq3 = st.columns(3)
        with sq1:
            if st.button("Terminated without notice?", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Can my employer terminate me without notice?"})
                st.rerun()
        with sq2:
            if st.button("Landlord keeps my deposit?", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "My landlord refuses to return my security deposit. What are my options?"})
                st.rerun()
        with sq3:
            if st.button("My rights if arrested?", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "What are my rights if I am arrested?"})
                st.rerun()

    # Chat Area
    chat_container = st.container(height=500, border=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Hello! I am VERDICT. How can I assist you with Philippine law today?")
            
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="⚖️" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    # Chat Input (Placed at the bottom of the middle column)
    if prompt := st.chat_input("Ask a question about Philippine law..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
                
            with st.chat_message("assistant", avatar="⚖️"):
                with st.spinner("VERDICT is analyzing..."):
                    max_retries = 3
                    reply = ""
                    for attempt in range(max_retries):
                        try:
                            response = client.models.generate_content(
                                model=MODEL_NAME,
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    system_instruction=VERDICT_SYSTEM_PROMPT
                                )
                            )
                            reply = response.text
                            break
                        except Exception as e:
                            error_msg = str(e)
                            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                                if attempt < max_retries - 1:
                                    st.info(f"Servers busy. Retrying ({attempt + 1}/{max_retries})...")
                                    time.sleep(3)
                                else:
                                    reply = "⚠️ Google servers are experiencing high demand. Please try again."
                            else:
                                reply = f"⚠️ Error: `{error_msg}`"
                                break
                    st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Force a rerun to clean up the UI state after generating
        st.rerun()

# ==========================================
# RIGHT COLUMN (Situation & References)
# ==========================================
with col_right:
    # Legal Situation Input Form
    with st.container(border=True):
        st.markdown("### Legal Situation Input")
        st.selectbox("CATEGORY", ["Labor / Civil / Criminal", "Civil / Housing", "Labor / Employment", "Criminal Law", "Personal / Family"])
        st.text_area("Facts of the situation", height=100)
        st.checkbox("Show both sides' arguments")
        st.file_uploader("Attach document (optional)", label_visibility="collapsed")
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.button("Analyze Situation", use_container_width=True, type="primary")
        with btn_col2:
            st.button("Prepare for Lawyer", use_container_width=True)
            
    # Legal References
    with st.container(border=True):
        st.markdown("### Legal References")
        
        st.markdown("📜 **LAW**")
        st.caption("Labor Code of the Philippines")
        st.divider()
        
        st.markdown("⚖️ **CASE**")
        st.caption("G.R. No. 123456")
        st.divider()
        
        st.markdown("📰 **GAZETTE**")
        st.caption("Official Gazette Vol. 1")