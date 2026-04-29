import time
from datetime import datetime, timezone
from loguru import logger
from src.models.schema import TriageOutput
from src.models.fallback import safe_fallback_output


def node_validate_schema(state: dict) -> dict:
    """Node 7: Pydantic schema validation — constructs TriageOutput from AgentState."""
    try:
        processing_start = state.get("processing_start_ms", 0)
        processing_time = int(time.time() * 1000) - processing_start if processing_start else 0

        # Calculate overall confidence
        intent_conf = state.get("intent_confidence", 0.0)
        faithfulness = state.get("faithfulness_score", 0.0)
        confidence = round((intent_conf + faithfulness) / 2, 2)

        try:
            output = TriageOutput(
                message_id=state.get("message_id", "unknown"),
                timestamp=datetime.now(timezone.utc).isoformat(),
                detected_language=state.get("detected_language", "en"),
                lang_confidence=state.get("lang_confidence", 0.0),
                normalized_text=state.get("normalized_text", "unknown")[:2100],
                intent=state.get("intent", "general_inquiry"),
                intent_confidence=intent_conf,
                urgency=state.get("urgency", "low"),
                urgency_score=state.get("urgency_score", 0.0),
                rag_chunks_used=state.get("rag_chunks", [])[:3],
                rag_grounded=state.get("rag_grounded", False),
                reply_en=state.get("reply_en", ""),
                reply_ar=state.get("reply_ar", ""),
                faithfulness_score=faithfulness,
                reflection_retries=state.get("reflection_retries", 0),
                escalate=state.get("escalate", False),
                escalation_reason=state.get("escalation_reason"),
                schema_valid=True,
                confidence=confidence,
                processing_time_ms=processing_time,
            )

            logger.info(f"Node 7: Schema valid ✓ (processing_time={processing_time}ms)")
            return {
                "final_output": output.model_dump(),
                "schema_valid": True,
            }

        except Exception as e:
            logger.error(f"Node 7: Pydantic validation failed: {e}")
            fallback = safe_fallback_output(
                message_id=state.get("message_id", "unknown"),
                raw_input=state.get("raw_input", ""),
            )
            fallback.processing_time_ms = processing_time
            return {
                "final_output": fallback.model_dump(),
                "schema_valid": False,
            }

    except Exception as e:
        logger.error(f"Node 7 catastrophic failure: {e}")
        fallback = safe_fallback_output(
            message_id=state.get("message_id", "unknown"),
            raw_input=state.get("raw_input", ""),
        )
        return {
            "final_output": fallback.model_dump(),
            "schema_valid": False,
            "error": str(e),
        }
