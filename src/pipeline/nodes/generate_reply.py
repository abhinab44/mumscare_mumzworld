import re
from loguru import logger
from src.models.fallback import (
    SAFE_MEDICAL_REPLY_EN, SAFE_MEDICAL_REPLY_AR,
    SAFE_FALLBACK_EN, SAFE_FALLBACK_AR,
)

# Post-generation safety patterns (medication names, dosage advice)
FORBIDDEN_PATTERNS_EN = [
    r"\b(paracetamol|ibuprofen|panadol|calpol|antihistamine|tylenol|advil)\b",
    r"\bgive (him|her|the baby|your child) \w+",
    r"\b(safe|okay|fine|normal) (dose|dosage|amount)\b",
    r"system prompt",
    r"ignore.*instructions",
]


def check_reply_safety(reply_en: str) -> bool:
    """Returns True if reply is safe (no medication names, no dosage advice)."""
    for pattern in FORBIDDEN_PATTERNS_EN:
        if re.search(pattern, reply_en.lower()):
            return False
    return True


def node_generate_reply(state: dict) -> dict:
    """Node 5: Reply generation (bilingual EN + AR)."""
    try:
        # If injection was detected, replies were already set in Node 2
        if state.get("injection_detected"):
            return {}

        normalized_text = state.get("normalized_text", "")
        language = state.get("detected_language", "en")
        intent = state.get("intent", "general_inquiry")
        urgency = state.get("urgency", "medium")
        rag_chunks = state.get("rag_chunks", [])
        rag_grounded = state.get("rag_grounded", False)
        retry_issues = state.get("reflection_issues", "")

        # Medical/safety override: use safe template directly
        if intent == "medical_concern" and urgency in ("high", "critical"):
            logger.info("Node 5: Medical concern → using safe medical reply template")
            return {
                "reply_en": SAFE_MEDICAL_REPLY_EN,
                "reply_ar": SAFE_MEDICAL_REPLY_AR,
            }

        try:
            from src.llm.groq_client import generate_reply
            result = generate_reply(
                text=normalized_text,
                language=language,
                intent=intent,
                urgency=urgency,
                rag_chunks=rag_chunks,
                rag_grounded=rag_grounded,
                retry_issues=retry_issues,
            )

            reply_en = result.get("reply_en", "")
            reply_ar = result.get("reply_ar", "")

            # Validate non-empty
            if not reply_en or len(reply_en) < 10:
                reply_en = SAFE_FALLBACK_EN
            if not reply_ar or len(reply_ar) < 10:
                reply_ar = SAFE_FALLBACK_AR

            # Post-generation safety check
            if not check_reply_safety(reply_en):
                logger.warning("Node 5: Reply failed safety check, using safe medical reply")
                return {
                    "reply_en": SAFE_MEDICAL_REPLY_EN,
                    "reply_ar": SAFE_MEDICAL_REPLY_AR,
                }

            logger.info(f"Node 5: Generated reply (en={len(reply_en)} chars, ar={len(reply_ar)} chars)")
            return {
                "reply_en": reply_en,
                "reply_ar": reply_ar,
            }

        except Exception as e:
            logger.warning(f"LLM generation failed: {e}, using fallback")
            return {
                "reply_en": SAFE_FALLBACK_EN,
                "reply_ar": SAFE_FALLBACK_AR,
            }

    except Exception as e:
        logger.error(f"Node 5 failed: {e}")
        return {
            "reply_en": SAFE_FALLBACK_EN,
            "reply_ar": SAFE_FALLBACK_AR,
            "error": str(e),
        }
