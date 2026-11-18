"""UI pieces for VERDICT. Each function draws one part of the page."""

import html

import streamlit as st

from services import chat, documents, export

SUGGESTED_QUESTIONS = [
    ("I was fired without notice.", "I was terminated without notice. What are my rights?", "sq_terminated"),
    ("My landlord kept my deposit.", "My landlord refuses to return my security deposit. What are my options?", "sq_deposit"),
    ("I was arrested. What now?", "I was arrested. What are my rights?", "sq_arrested"),
]


# ---------- Header ----------

def render_header():
    """Logo, title, Clear and Settings buttons, and the settings panel."""
    col_title, col_btn1, col_btn2 = st.columns([5.5, 1.3, 1.1])
    with col_title:
        st.markdown(
            "<div class='verdict-brand'>"
            "<div class='verdict-logo'>⚖️</div>"
            "<div>"
            "<div class='verdict-title'>VERDICT</div>"
            "<div class='verdict-subtitle'>\"I keep my eyes open.\"</div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col_btn1:
        if st.button("Clear the Record", use_container_width=True, key="header_clear"):
            chat.clear_conversation()
            st.rerun()
    with col_btn2:
        if st.button("Settings", use_container_width=True, key="header_settings"):
            st.session_state.show_settings = not st.session_state.get("show_settings", False)

    if st.session_state.get("show_settings"):
        render_settings()

    st.markdown("<hr/>", unsafe_allow_html=True)


def render_settings():
    """Settings panel: lets the user change the Gemini model."""
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Settings</div>", unsafe_allow_html=True)
        new_model = st.text_input("Model name", value=st.session_state.model_name, key="settings_model")
        if new_model and new_model != st.session_state.model_name:
            st.session_state.model_name = new_model
        st.caption(f"Model: `{st.session_state.model_name}`")
        st.caption("Session state is cleared on Clear the Record.")


# ---------- Left column ----------

def render_navigation():
    """Mode buttons, jurisdiction filters, sources, and the disclaimer."""
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Proceedings</div>", unsafe_allow_html=True)
        for mode in chat.MODE_PROMPTS:
            is_active = st.session_state.mode == mode
            if st.button(
                chat.MODE_LABELS.get(mode, mode),
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


# ---------- Middle column ----------

def render_mode_banner():
    """Shows which mode is active and what it does."""
    mode = st.session_state.mode
    st.markdown(
        "<div class='mode-banner'>"
        "<span class='mode-tag'>Now in</span>"
        f"<span class='mode-name'>{html.escape(chat.MODE_LABELS.get(mode, mode))}</span>"
        f"<span class='mode-desc'>{html.escape(chat.MODE_DESCRIPTIONS.get(mode, ''))}</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_chat():
    """Suggested questions, the message history, and the chat input.

    Returns the history container so a new reply can be streamed into it.
    """
    with st.container(border=True):
        render_mode_banner()
        st.markdown("<div class='section-label'>Counsel suggests</div>", unsafe_allow_html=True)
        columns = st.columns(len(SUGGESTED_QUESTIONS))
        for column, (label, question, key) in zip(columns, SUGGESTED_QUESTIONS):
            with column:
                if st.button(label, use_container_width=True, key=key):
                    chat.add_user_message(question)
                    st.rerun()

    history = st.container(height=520, border=True)
    with history:
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
        chat.add_user_message(prompt)
        st.rerun()

    return history


def _hide_when_started(stream, status):
    """Pass the stream through, clearing the status line once text arrives."""
    started = False
    for piece in stream:
        if not started:
            status.empty()
            started = True
        yield piece


def render_streaming_reply(history):
    """Show Gemini's answer word by word inside the chat history, then save it."""
    with history:
        with st.chat_message("assistant", avatar="🔨"):
            status = st.empty()
            status.caption("Reviewing the facts...")
            try:
                reply = st.write_stream(_hide_when_started(chat.reply_stream(), status))
            except chat.GeminiError as error:
                chat.save_error(error)
                return
    chat.save_reply(reply)


# ---------- Right column ----------

def render_case_file():
    """Case File form: category, facts, document upload, Analyze and Lawyer Prep."""
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Case File</div>", unsafe_allow_html=True)
        st.selectbox("Category", chat.CATEGORY_OPTIONS, key="right_category")
        facts = st.text_area(
            "Facts of the situation",
            height=110,
            placeholder="Describe what happened. In order. Without omitting anything.",
            key="right_facts",
        )
        st.checkbox("Show both sides' arguments", key="right_both_sides")
        uploaded = st.file_uploader(
            "Attach document (optional)",
            type=documents.SUPPORTED_TYPES,
            label_visibility="collapsed",
            key="right_upload",
        )
        document = documents.read_document(uploaded)
        render_document_status(document)

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Analyze", use_container_width=True, type="primary", key="right_analyze"):
                if not facts.strip():
                    st.warning("You have given me nothing to work with. State the facts first.")
                else:
                    st.session_state.mode = "Situation Analysis"
                    context = chat.build_analysis_context(
                        category=st.session_state.right_category,
                        both_sides=st.session_state.right_both_sides,
                        document=document,
                    )
                    chat.add_user_message(facts, context)
                    st.rerun()
        with btn_col2:
            if st.button("Lawyer Prep", use_container_width=True, key="right_lawyer_prep"):
                if not facts.strip():
                    st.warning("I cannot prepare a case from silence. Give me the facts.")
                else:
                    st.session_state.mode = "Lawyer Prep"
                    chat.add_user_message(facts, chat.build_lawyer_prep_context(document))
                    st.rerun()


def render_document_status(document):
    """Tell the user whether the attached document was read, with a preview."""
    if document is None:
        return  # the uploader already lists the accepted file types
    if document.error:
        st.warning(f"{document.name}: {document.error}")
        return

    if document.truncated:
        st.caption(
            f"📎 {document.name} — first {len(document.text):,} of "
            f"{document.total_chars:,} characters will be used."
        )
    else:
        st.caption(f"📎 {document.name} — {document.total_chars:,} characters read.")
    with st.expander("Preview extracted text"):
        st.text(document.text[:800] + ("..." if len(document.text) > 800 else ""))


def render_citations():
    """Citations found in the latest reply, each linked to a search on Lawphil."""
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Citations</div>", unsafe_allow_html=True)
        citations = st.session_state.last_references
        if not citations:
            st.caption("Citations from the latest exchange will appear here.")
            return

        rows = []
        for citation in citations:
            kind = citation["kind"]
            rows.append(
                "<div class='cite'>"
                f"<span class='cite-kind {kind.lower()}'>{html.escape(kind)}</span>"
                f"<a href='{html.escape(citation['url'])}' target='_blank' rel='noopener'>"
                f"{html.escape(citation['label'])}</a>"
                "</div>"
            )
        st.markdown(f"<div class='cite-list'>{''.join(rows)}</div>", unsafe_allow_html=True)
        st.caption("Links open a search on Lawphil. Always check the full text.")


def render_export():
    """Download buttons for the conversation, as Word or plain text."""
    with st.container(border=True):
        st.markdown("<div class='nav-label'>Export the Record</div>", unsafe_allow_html=True)
        messages = export.exportable_messages(st.session_state.messages)
        if not messages:
            st.caption("Your conversation can be downloaded once it starts.")
            return

        args = (st.session_state.messages, st.session_state.mode, st.session_state.last_references)
        col_word, col_text = st.columns(2)
        with col_word:
            st.download_button(
                "Word (.docx)",
                data=export.build_docx(*args),
                file_name=export.file_name("docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="export_docx",
            )
        with col_text:
            st.download_button(
                "Text (.txt)",
                data=export.build_text(*args),
                file_name=export.file_name("txt"),
                mime="text/plain",
                use_container_width=True,
                key="export_txt",
            )
        st.caption("Bring this to your lawyer, especially after Lawyer Prep.")