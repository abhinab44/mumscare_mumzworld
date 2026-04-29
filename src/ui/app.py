"""
MomCare Triage Agent — Streamlit UI
Main entry point: streamlit run src/ui/app.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from src.ui.styles import inject_global_css
from src.ui.components.header import render_header
from src.ui.components.chat_message import render_bot_message, render_user_message, render_welcome_message
from src.ui.components.triage_panel import render_triage_panel
from src.ui.components.language_toggle import render_language_toggle

# Page config
st.set_page_config(
    page_title="MomCare — Mumzworld Support",
    page_icon="🙂",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Inject CSS
inject_global_css()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_output" not in st.session_state:
    st.session_state.last_output = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "processing" not in st.session_state:
    st.session_state.processing = False
if "chroma_seeded" not in st.session_state:
    st.session_state.chroma_seeded = False

# Auto-seed ChromaDB on first run
if not st.session_state.chroma_seeded:
    try:
        from src.rag.client import is_seeded
        if not is_seeded():
            with st.spinner("🔄 Setting up policy database (one-time)..."):
                from scripts.seed_chroma import seed_chroma
                seed_chroma()
        st.session_state.chroma_seeded = True
    except Exception as e:
        st.warning(f"ChromaDB setup note: {e}. RAG may be limited.")
        st.session_state.chroma_seeded = True

# Render header
render_header()

# Language toggle
lang = render_language_toggle()

# Divider
st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

# Render chat history
if not st.session_state.messages:
    render_welcome_message(lang)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        render_user_message(msg["content"])
    else:
        is_arabic = msg.get("is_arabic", False)
        if is_arabic and lang == "ar":
            render_bot_message(msg.get("content_ar", msg["content"]), is_arabic=True)
        else:
            render_bot_message(msg["content"], is_arabic=False)

        # Show triage panel for the last message
        if msg.get("output"):
            render_triage_panel(msg["output"], lang)

# Chat input
placeholder = "اكتب سؤالك هنا..." if lang == "ar" else "Type your question here..."
if prompt := st.chat_input(placeholder=placeholder):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })
    render_user_message(prompt)

    # Process with pipeline
    with st.spinner("🙂 Maya is thinking..." if lang == "en" else "🙂 مايا تفكر..."):
        try:
            from src.pipeline.graph import run_triage
            output = run_triage(prompt)
            output_dict = output.model_dump()

            # Determine display language
            is_arabic = output.detected_language == "ar" or lang == "ar"

            if is_arabic:
                display_content = output.reply_ar
            else:
                display_content = output.reply_en

            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": output.reply_en,
                "content_ar": output.reply_ar,
                "is_arabic": is_arabic,
                "output": output_dict,
            })
            st.session_state.last_output = output_dict

            # Render response
            render_bot_message(display_content, is_arabic=is_arabic)
            render_triage_panel(output_dict, lang)

        except Exception as e:
            error_msg = f"I'm sorry, something went wrong. Please try again. (Error: {str(e)[:100]})"
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "is_arabic": False,
                "output": None,
            })
            render_bot_message(error_msg)

    st.rerun()
