import re
import html
import os
from loguru import logger

MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))

INJECTION_PATTERNS = [
    r"ignore (all |previous |prior )(instructions?|prompts?|rules?)",
    r"you are now (DAN|an? AI without|a jailbroken)",
    r"(reveal|show|output|print) (your |the )?(system prompt|instructions|rules)",
    r"(pretend|roleplay|act as|imagine) (you are|you're) (a |an )?(different|unrestricted|human)",
    r"(bypass|disable|override) (safety|restrictions|guidelines|filters)",
    r"(forget|disregard) (everything|all) (above|before|previously)",
    r"with no restrictions",
]


def detect_injection(text: str) -> bool:
    """Detect prompt injection attempts via regex patterns."""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in INJECTION_PATTERNS)


def detect_language(text: str) -> tuple:
    """
    Detect language from text using langdetect + Arabic Unicode heuristic.
    Returns (language_code, confidence).
    """
    try:
        # Arabic Unicode heuristic: if >30% of chars are Arabic → force "ar"
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        total_chars = len(re.findall(r'\S', text))
        if total_chars > 0 and arabic_chars / total_chars > 0.3:
            return "ar", 0.95

        from langdetect import detect_langs
        langs = detect_langs(text)
        if langs:
            top = langs[0]
            lang_code = str(top.lang)
            confidence = top.prob

            if lang_code == "ar":
                return "ar", confidence
            elif confidence < 0.6:
                logger.warning(f"Low language confidence ({confidence:.2f}), defaulting to EN")
                return "en", confidence
            else:
                return "en", confidence
        return "en", 0.5
    except Exception as e:
        logger.warning(f"Language detection failed: {e}, defaulting to EN")
        return "en", 0.0


def node_detect_normalize(state: dict) -> dict:
    """Node 1: Language detection, input normalization, injection detection."""
    try:
        raw_input = state.get("raw_input", "")

        # Step 1: Check for empty/too-short input
        if not raw_input or not raw_input.strip():
            return {
                "detected_language": "en",
                "lang_confidence": 0.0,
                "normalized_text": "help",
                "injection_detected": False,
            }

        # Step 2: Remove null bytes and control characters
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', raw_input)

        # Step 3: Unescape HTML entities
        cleaned = html.unescape(cleaned)

        # Step 4: Truncate to max length
        cleaned = cleaned[:MAX_INPUT_LENGTH]

        # Step 5: Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Step 6: Injection detection
        injection_detected = detect_injection(cleaned)
        if injection_detected:
            logger.warning(f"Prompt injection detected in input")
            return {
                "detected_language": "en",
                "lang_confidence": 1.0,
                "normalized_text": cleaned,
                "injection_detected": True,
                "escalate": True,
                "escalation_reason": "safety",
            }

        # Step 7: Language detection
        lang, confidence = detect_language(cleaned)

        logger.info(f"Node 1: lang={lang}, confidence={confidence:.2f}, len={len(cleaned)}")

        return {
            "detected_language": lang,
            "lang_confidence": confidence,
            "normalized_text": cleaned,
            "injection_detected": False,
        }

    except Exception as e:
        logger.error(f"Node 1 failed: {e}")
        return {
            "detected_language": "en",
            "lang_confidence": 0.0,
            "normalized_text": state.get("raw_input", "help")[:500],
            "injection_detected": False,
            "error": str(e),
        }
