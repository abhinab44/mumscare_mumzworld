import streamlit as st


def inject_global_css():
    """Inject Mumzworld-branded CSS tokens and global styling."""
    st.markdown("""
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* CSS Custom Properties */
        :root {
            --color-primary: #E8175D;
            --color-primary-light: #FFE4EE;
            --color-primary-dark: #C41050;
            --color-text-main: #2D2D2D;
            --color-text-secondary: #6B6B6B;
            --color-white: #FFFFFF;
            --color-border: #E8E8E8;
            --color-bg-subtle: #FFF8FA;
            --font-primary: 'Inter', 'Segoe UI', Tahoma, Arial, sans-serif;
            --font-size-body: 15px;
            --font-size-heading: 18px;
            --border-radius-card: 12px;
            --border-radius-pill: 24px;
            --shadow-card: 0 2px 8px rgba(0,0,0,0.08);
            --spacing-sm: 8px;
            --spacing-md: 16px;
        }

        /* Mobile-first container */
        .main .block-container {
            max-width: 520px;
            margin: 0 auto;
            padding: 0 12px;
            font-family: var(--font-primary);
        }

        /* Global font */
        html, body, [class*="css"] {
            font-family: var(--font-primary);
        }

        /* Pink primary buttons */
        .stButton button[kind="primary"],
        .stButton button[data-testid="baseButton-primary"] {
            background-color: var(--color-primary) !important;
            border: none !important;
            border-radius: var(--border-radius-pill) !important;
            color: white !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }
        .stButton button[kind="primary"]:hover,
        .stButton button[data-testid="baseButton-primary"]:hover {
            background-color: var(--color-primary-dark) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(232, 23, 93, 0.3);
        }

        /* Secondary buttons */
        .stButton button[kind="secondary"],
        .stButton button[data-testid="baseButton-secondary"] {
            background-color: var(--color-white) !important;
            border: 1.5px solid var(--color-border) !important;
            border-radius: var(--border-radius-pill) !important;
            color: var(--color-text-main) !important;
            font-weight: 500 !important;
            transition: all 0.2s ease;
        }
        .stButton button[kind="secondary"]:hover,
        .stButton button[data-testid="baseButton-secondary"]:hover {
            border-color: var(--color-primary) !important;
            color: var(--color-primary) !important;
        }

        /* Chat input styling */
        .stChatInput textarea {
            border-radius: var(--border-radius-pill) !important;
            border-color: var(--color-primary) !important;
            font-family: var(--font-primary);
            font-size: var(--font-size-body);
        }
        .stChatInput textarea:focus {
            box-shadow: 0 0 0 2px rgba(232, 23, 93, 0.2) !important;
        }

        /* Chat message bubbles */
        [data-testid="stChatMessage"] {
            background: transparent !important;
        }
        [data-testid="stChatMessageContent"] {
            border-radius: var(--border-radius-card) !important;
            font-family: var(--font-primary);
            font-size: var(--font-size-body);
            line-height: 1.6;
        }

        /* Assistant messages - pink tint */
        .stChatMessage[data-testid="chat-message-assistant"] [data-testid="stChatMessageContent"] {
            background: var(--color-primary-light) !important;
            color: var(--color-text-main);
        }

        /* User messages */
        .stChatMessage[data-testid="chat-message-user"] [data-testid="stChatMessageContent"] {
            background: #F0F0F5 !important;
        }

        /* Hide Streamlit defaults */
        #MainMenu, footer, header { visibility: hidden; }

        /* Metric labels */
        [data-testid="stMetricLabel"] {
            font-size: 11px !important;
            color: var(--color-text-secondary);
        }
        [data-testid="stMetricValue"] {
            font-size: 16px !important;
            font-weight: 600;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            font-family: var(--font-primary);
            font-weight: 600;
            color: var(--color-text-main);
            background: var(--color-bg-subtle);
            border-radius: var(--border-radius-card);
        }

        /* RTL support for Arabic */
        .rtl-text {
            direction: rtl;
            text-align: right;
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            line-height: 1.8;
            color: var(--color-text-main);
            font-size: 15px;
        }

        /* Escalation banner */
        .escalation-banner {
            background: linear-gradient(135deg, #FFE4EE 0%, #FFF0F5 100%);
            border-left: 4px solid var(--color-primary);
            border-radius: 0 var(--border-radius-card) var(--border-radius-card) 0;
            padding: 12px 16px;
            margin: 8px 0;
            font-family: var(--font-primary);
        }

        /* Urgency badges */
        .urgency-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: var(--border-radius-pill);
            font-size: 12px;
            font-weight: 600;
        }
        .urgency-low { background: #E8F5E9; color: #2E7D32; }
        .urgency-medium { background: #FFF3E0; color: #EF6C00; }
        .urgency-high { background: #FFF3E0; color: #E65100; }
        .urgency-critical { background: #FFEBEE; color: #C62828; }

        /* Scrollbar styling */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)
