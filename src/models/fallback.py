from datetime import datetime, timezone
from src.models.schema import TriageOutput


SAFE_FALLBACK_EN = (
    "Thank you for reaching out to Mumzworld! We've received your message "
    "and a member of our support team will get back to you shortly. "
    "For urgent matters, please contact us at support@mumzworld.com."
)

SAFE_FALLBACK_AR = (
    "شكراً لتواصلك مع ممزورلد! وصلتنا رسالتك وسيتواصل معك أحد أعضاء فريق الدعم قريباً. "
    "للأمور العاجلة، يمكنك التواصل معنا على support@mumzworld.com"
)

SAFE_MEDICAL_REPLY_EN = (
    "We're concerned about your child's wellbeing. Please contact a doctor or "
    "emergency services immediately — UAE: 998, KSA: 911. Do not wait for online advice. "
    "Once your child is safe, our team can help with any product-related concerns."
)

SAFE_MEDICAL_REPLY_AR = (
    "نحن قلقون على سلامة طفلك. يرجى التواصل مع الطبيب أو خدمات الطوارئ فوراً — "
    "الإمارات: 998، السعودية: 911. لا تنتظروا النصائح عبر الإنترنت. "
    "بعد اطمئنانكم على سلامة الطفل، فريقنا جاهز لمساعدتكم في أي مخاوف متعلقة بالمنتج."
)

INJECTION_REFUSAL_EN = (
    "I'm not able to help with that request. If you have a question about "
    "your Mumzworld order or account, I'm happy to assist!"
)

INJECTION_REFUSAL_AR = (
    "لا أستطيع المساعدة في هذا الطلب. إذا كان لديك سؤال عن طلبك أو حسابك "
    "في ممزورلد، يسعدني مساعدتك!"
)


def safe_fallback_output(message_id: str, raw_input: str) -> TriageOutput:
    return TriageOutput(
        message_id=message_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        detected_language="en",
        lang_confidence=0.0,
        normalized_text=raw_input[:500] if raw_input else "empty",
        intent="general_inquiry",
        intent_confidence=0.0,
        urgency="low",
        urgency_score=0.0,
        rag_chunks_used=[],
        rag_grounded=False,
        reply_en=SAFE_FALLBACK_EN,
        reply_ar=SAFE_FALLBACK_AR,
        faithfulness_score=1.0,
        reflection_retries=0,
        escalate=True,
        escalation_reason="low_confidence",
        schema_valid=False,
        confidence=0.0,
        processing_time_ms=0,
    )
