import re
from loguru import logger
from src.models.fallback import INJECTION_REFUSAL_EN, INJECTION_REFUSAL_AR


# Keyword fallback classifier (used when LLM fails)
KEYWORD_RULES = {
    "order_status": ["order", "delivery", "tracking", "shipped", "arrived", "deliver", "طلب", "توصيل", "شحن"],
    "return_refund": ["return", "refund", "exchange", "money back", "إرجاع", "استرجاع", "استرداد"],
    "product_query": ["product", "suitable", "age", "brand", "recommend", "منتج", "مناسب"],
    "account_issue": ["login", "password", "account", "locked", "wallet", "حساب", "كلمة المرور", "محفظة"],
    "medical_concern": ["rash", "fever", "breathing", "allergic", "medicine", "doctor", "symptom",
                        "حساسية", "طوارئ", "دكتور", "طبيب", "دواء", "ألم"],
    "complaint": ["worst", "terrible", "angry", "useless", "compensation", "unacceptable"],
}


def keyword_classify(text: str) -> tuple:
    """Fallback keyword-based intent classifier."""
    text_lower = text.lower()
    for intent, keywords in KEYWORD_RULES.items():
        if any(kw in text_lower for kw in keywords):
            return intent, 0.6
    return "general_inquiry", 0.4


def node_classify_intent(state: dict) -> dict:
    """Node 2: Intent classification via LLM with keyword fallback."""
    try:
        # If injection was detected in Node 1, short-circuit
        if state.get("injection_detected"):
            logger.info("Node 2: Injection detected, returning complaint + refusal")
            return {
                "intent": "complaint",
                "intent_confidence": 0.25,
                "escalate": True,
                "escalation_reason": "safety",
                "reply_en": INJECTION_REFUSAL_EN,
                "reply_ar": INJECTION_REFUSAL_AR,
            }

        normalized_text = state.get("normalized_text", "")

        try:
            from src.llm.groq_client import classify_intent
            result = classify_intent(normalized_text)
            intent = result.get("intent", "general_inquiry")
            confidence = float(result.get("confidence", 0.5))

            # Validate intent is a known class
            valid_intents = ["order_status", "return_refund", "product_query",
                           "account_issue", "medical_concern", "complaint", "general_inquiry"]
            if intent not in valid_intents:
                logger.warning(f"Unknown intent '{intent}', falling back to keyword")
                intent, confidence = keyword_classify(normalized_text)

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}, using keyword fallback")
            intent, confidence = keyword_classify(normalized_text)

        # Post-processing: low confidence → general_inquiry
        updates = {
            "intent": intent,
            "intent_confidence": confidence,
        }

        if confidence < 0.55 and intent != "medical_concern":
            logger.info(f"Low confidence ({confidence:.2f}), treating as general_inquiry")
            updates["intent"] = "general_inquiry"

        logger.info(f"Node 2: intent={updates['intent']}, confidence={confidence:.2f}")
        return updates

    except Exception as e:
        logger.error(f"Node 2 failed: {e}")
        return {
            "intent": "general_inquiry",
            "intent_confidence": 0.0,
            "error": str(e),
        }
