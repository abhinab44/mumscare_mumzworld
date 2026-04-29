import streamlit as st


def render_header():
    """Render the Mumzworld-branded header bar."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #E8175D 0%, #D81557 100%);
        padding: 14px 20px;
        border-radius: 0 0 16px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(232, 23, 93, 0.2);
    ">
        <span style="color: white; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
            🙂 mumzworld
        </span>
        <span style="color: rgba(255,255,255,0.9); font-size: 13px; font-weight: 500;">
            💬 Help 24/7 &nbsp; ♡
        </span>
    </div>
    """, unsafe_allow_html=True)
