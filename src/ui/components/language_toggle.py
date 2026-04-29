import streamlit as st


def render_language_toggle():
    """Render EN/AR language toggle buttons. Returns current language."""
    col1, col2 = st.columns([1, 1])

    lang = st.session_state.get("language", "en")

    with col1:
        if st.button(
            "🌐 English",
            use_container_width=True,
            type="primary" if lang == "en" else "secondary",
            key="lang_en"
        ):
            st.session_state.language = "en"
            st.rerun()

    with col2:
        if st.button(
            "العربية",
            use_container_width=True,
            type="primary" if lang == "ar" else "secondary",
            key="lang_ar"
        ):
            st.session_state.language = "ar"
            st.rerun()

    return st.session_state.get("language", "en")
