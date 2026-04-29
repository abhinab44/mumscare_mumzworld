import re
from loguru import logger

# Instant critical keywords (Layer 1)
CRITICAL_KEYWORDS_EN = [
    "allergic reaction", "can't breathe", "cannot breathe", "emergency",
    "bleeding", "fell down", "swallowed", "unconscious", "choking",
    "stopped breathing", "not breathing", "poisoning",
]
CRITICAL_KEYWORDS_AR = [
    "حساسية شديدة", "طوارئ", "نزيف", "ابتلع", "اختناق",
    "فقد الوعي", "صعوبة في التنفس", "تسمم",
]

# Medical keyword detection (Layer 2 - SECURITY.md)
MEDICAL_KEYWORDS = {
    "en": ["symptom", "rash", "fever", "breathe", "breathing", "allergic",
           "allergy", "medicine", "medication", "dose", "dosage", "doctor",
           "hospital", "emergency", "swallowed", "bleeding", "unconscious",
           "choking", "reaction", "pain", "hurt", "injured"],
    "ar": ["حساسية", "طوارئ", "دكتور", "طبيب", "مستشفى", "دواء", "علاج",
           "أعراض", "ألم", "إصابة", "نزيف", "ابتلع", "صعوبة في التنفس"],
}


def check_critical_keywords(text: str) -> bool:
    """Layer 1: Check for instant-critical keywords."""
    text_lower = text.lower()
    for kw in CRITICAL_KEYWORDS_EN + CRITICAL_KEYWORDS_AR:
        if kw in text_lower:
            return True
    return False


def check_medical_keywords(text: str, lang: str) -> bool:
    """Layer 2: Check for medical keywords."""
    text_lower = text.lower()
    keywords = MEDICAL_KEYWORDS.get(lang, MEDICAL_KEYWORDS["en"])
    return any(kw in text_lower for kw in keywords)


def score_to_label(score: float) -> str:
    """Map urgency score to label."""
    if score >= 0.85:
        return "critical"
    elif score >= 0.65:
        return "high"
    elif score >= 0.3:
        return "medium"
    else:
        return "low"


def node_score_urgency(state: dict) -> dict:
    """Node 3: Urgency scoring with keyword rules, LLM scoring, and safety overrides."""
    try:
        normalized_text = state.get("normalized_text", "")
        intent = state.get("intent", "general_inquiry")
        lang = state.get("detected_language", "en")

        # If injection was already detected, skip urgency scoring
        if state.get("injection_detected"):
            return {
                "urgency": "low",
                "urgency_score": 0.1,
            }

        # Layer 1: Instant critical keywords
        if check_critical_keywords(normalized_text):
            logger.info("Node 3: Critical keyword detected → urgency=critical")
            return {
                "urgency": "critical",
                "urgency_score": 0.95,
                "escalate": True,
                "escalation_reason": "safety",
            }

        # Layer 2: LLM urgency scoring
        urgency_score = 0.3  # default medium
        try:
            from src.llm.groq_client import score_urgency
            result = score_urgency(normalized_text, intent)
            urgency_score = float(result.get("urgency_score", 0.3))
            urgency_score = max(0.0, min(1.0, urgency_score))
        except Exception as e:
            logger.warning(f"LLM urgency scoring failed: {e}, using default")
            # Heuristic fallback
            if intent == "complaint":
                urgency_score = 0.65
            elif intent in ["order_status", "return_refund"]:
                urgency_score = 0.4
            elif intent == "medical_concern":
                urgency_score = 0.9

        # Layer 3: Safety overrides
        urgency_label = score_to_label(urgency_score)
        escalate = state.get("escalate", False)
        escalation_reason = state.get("escalation_reason")

        # Medical concern → minimum high
        if intent == "medical_concern":
            if urgency_score < 0.6:
                urgency_score = 0.85
            urgency_label = score_to_label(urgency_score)
            if urgency_label not in ("high", "critical"):
                urgency_label = "high"
                urgency_score = max(urgency_score, 0.7)
            escalate = True
            escalation_reason = "medical_concern"

        # Medical keywords also trigger escalation
        if check_medical_keywords(normalized_text, lang) and intent != "product_query":
            if urgency_score < 0.6:
                urgency_score = 0.7
                urgency_label = "high"
            escalate = True
            escalation_reason = escalation_reason or "medical_concern"

        # Critical urgency → always escalate
        if urgency_label == "critical":
            escalate = True
            escalation_reason = escalation_reason or "safety"

        # Complaint with high urgency → escalate
        if intent == "complaint" and urgency_label in ("high", "critical"):
            escalate = True
            escalation_reason = escalation_reason or "explicit_request"

        updates = {
            "urgency": urgency_label,
            "urgency_score": urgency_score,
        }
        if escalate:
            updates["escalate"] = True
            updates["escalation_reason"] = escalation_reason

        logger.info(f"Node 3: urgency={urgency_label}, score={urgency_score:.2f}, escalate={escalate}")
        return updates

    except Exception as e:
        logger.error(f"Node 3 failed: {e}")
        return {
            "urgency": "medium",
            "urgency_score": 0.4,
            "error": str(e),
        }
