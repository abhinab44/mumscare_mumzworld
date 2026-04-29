import streamlit as st


def render_bot_message(content: str, is_arabic: bool = False):
    """Render a bot (Maya) message with RTL support for Arabic."""
    with st.chat_message("assistant", avatar="🙂"):
        if is_arabic:
            st.markdown(f"""
            <div class="rtl-text" data-testid="arabic-reply">
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write(content)


def render_user_message(content: str):
    """Render a user message."""
    with st.chat_message("user"):
        st.write(content)


def render_welcome_message(language: str = "en"):
    """Render the initial welcome message from Maya."""
    if language == "ar":
        welcome = """
        <div class="rtl-text" data-testid="welcome-arabic">
            <strong>🙂 مايا</strong><br>
            أهلاً وسهلاً في ممزورلد! كيف أقدر أساعدك اليوم؟ 💝
        </div>
        """
    else:
        welcome = """
        <div data-testid="welcome-english">
            <strong>🙂 Maya</strong><br>
            Welcome to Mumzworld! How can I support you today? 💝
        </div>
        """

    with st.chat_message("assistant", avatar="🙂"):
        st.markdown(welcome, unsafe_allow_html=True)
