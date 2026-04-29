import streamlit as st


def render_triage_panel(output: dict, language: str = "en"):
    """Render the expandable triage details panel with metrics and JSON."""
    if not output:
        return

    label = "📊 تفاصيل التصنيف" if language == "ar" else "📊 Triage Details"

    with st.expander(label, expanded=False):
        # Row 1: Intent, Urgency, Confidence
        col1, col2, col3 = st.columns(3)

        intent_display = output.get("intent", "unknown").replace("_", " ").title()
        col1.metric("Intent", intent_display)

        urgency = output.get("urgency", "low")
        urgency_icons = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
        icon = urgency_icons.get(urgency, "⚪")
        col2.metric("Urgency", f"{icon} {urgency.title()}")

        confidence = output.get("confidence", 0)
        col3.metric("Confidence", f"{confidence:.0%}")

        # Row 2: Faithfulness, Language, Schema
        col4, col5, col6 = st.columns(3)

        faithfulness = output.get("faithfulness_score", 0)
        col4.metric("Faithfulness", f"{faithfulness:.2f}")

        lang = output.get("detected_language", "en")
        col5.metric("Language", lang.upper())

        schema_valid = output.get("schema_valid", False)
        col6.metric("Schema", "✅ Valid" if schema_valid else "❌ Failed")

        # Processing time
        proc_time = output.get("processing_time_ms", 0)
        st.caption(f"⏱️ Processing time: {proc_time}ms")

        # Escalation banner
        if output.get("escalate"):
            reason = output.get("escalation_reason", "unknown")
            reason_messages = {
                "medical_concern": "👩‍⚕️ This looks like a medical question — please consult a doctor immediately.",
                "safety": "⚠️ This has been flagged for our senior support team.",
                "faithfulness_failure": "🔄 Our agent couldn't find a confident answer — a human will follow up.",
                "low_confidence": "💬 Routing to our team for personalized help.",
                "explicit_request": "📢 Escalating to our support team as requested.",
            }
            msg = reason_messages.get(reason, "Our support team will be in touch.")
            st.markdown(f"""
            <div class="escalation-banner">
                ⚠️ <strong>Escalated</strong>: {msg}
            </div>
            """, unsafe_allow_html=True)

        # RAG chunks
        chunks = output.get("rag_chunks_used", [])
        if chunks:
            st.caption("📚 Policy context used:")
            for chunk in chunks:
                truncated = chunk[:150] + "..." if len(chunk) > 150 else chunk
                st.caption(f"• {truncated}")

        # Full JSON
        with st.expander("🔍 Full JSON Output"):
            st.json(output)
