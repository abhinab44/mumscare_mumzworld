import time
import uuid
import os
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, START, END
from src.pipeline.state import AgentState
from src.pipeline.nodes.detect_normalize import node_detect_normalize
from src.pipeline.nodes.classify_intent import node_classify_intent
from src.pipeline.nodes.score_urgency import node_score_urgency
from src.pipeline.nodes.rag_retrieve import node_rag_retrieve
from src.pipeline.nodes.generate_reply import node_generate_reply
from src.pipeline.nodes.self_reflect import node_self_reflect
from src.pipeline.nodes.validate_schema import node_validate_schema
from src.models.schema import TriageOutput
from src.models.fallback import safe_fallback_output

FAITHFULNESS_THRESHOLD = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.6"))
MAX_REFLECTION_RETRIES = int(os.getenv("MAX_REFLECTION_RETRIES", "2"))


def should_retry_or_validate(state: dict) -> str:
    """Conditional edge: retry generation if faithfulness low, else validate."""
    faithfulness = state.get("faithfulness_score", 1.0)
    retries = state.get("reflection_retries", 0)

    if faithfulness < FAITHFULNESS_THRESHOLD and retries < MAX_REFLECTION_RETRIES:
        logger.info(f"Faithfulness {faithfulness:.2f} < {FAITHFULNESS_THRESHOLD}, retrying (attempt {retries+1})")
        return "generate_reply"
    else:
        return "validate_schema"


def build_graph() -> StateGraph:
    """Build the 7-node LangGraph StateGraph for triage pipeline."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("detect_normalize", node_detect_normalize)
    graph.add_node("classify_intent", node_classify_intent)
    graph.add_node("score_urgency", node_score_urgency)
    graph.add_node("rag_retrieve", node_rag_retrieve)
    graph.add_node("generate_reply", node_generate_reply)
    graph.add_node("self_reflect", node_self_reflect)
    graph.add_node("validate_schema", node_validate_schema)

    # Add edges
    graph.add_edge(START, "detect_normalize")
    graph.add_edge("detect_normalize", "classify_intent")
    graph.add_edge("classify_intent", "score_urgency")
    graph.add_edge("score_urgency", "rag_retrieve")
    graph.add_edge("rag_retrieve", "generate_reply")
    graph.add_edge("generate_reply", "self_reflect")

    # Conditional edge on reflection
    graph.add_conditional_edges(
        "self_reflect",
        should_retry_or_validate,
        {"generate_reply": "generate_reply", "validate_schema": "validate_schema"}
    )

    graph.add_edge("validate_schema", END)

    return graph


# Compile once at module level
_compiled_graph = None


def get_compiled_graph():
    """Get or compile the triage graph."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


def run_triage(raw_input: str, message_id: str = None) -> TriageOutput:
    """
    Main entry point for the MomCare triage pipeline.

    Args:
        raw_input: Raw customer query string (EN or AR, 1-2000 chars)
        message_id: Optional UUID. Auto-generated if not provided.

    Returns:
        TriageOutput: Fully validated Pydantic model.
        On any unrecoverable error: returns safe_fallback_output()

    Raises:
        Never raises. All exceptions caught internally.
    """
    if not message_id:
        message_id = str(uuid.uuid4())

    start_ms = int(time.time() * 1000)

    try:
        compiled = get_compiled_graph()

        initial_state = {
            "raw_input": raw_input or "",
            "message_id": message_id,
            "detected_language": "en",
            "lang_confidence": 0.0,
            "normalized_text": "",
            "injection_detected": False,
            "intent": "general_inquiry",
            "intent_confidence": 0.0,
            "urgency": "low",
            "urgency_score": 0.0,
            "rag_chunks": [],
            "rag_scores": [],
            "rag_grounded": False,
            "reply_en": "",
            "reply_ar": "",
            "faithfulness_score": 0.0,
            "reflection_retries": 0,
            "reflection_passed": False,
            "reflection_issues": "",
            "final_output": None,
            "schema_valid": False,
            "escalate": False,
            "escalation_reason": None,
            "error": None,
            "processing_start_ms": start_ms,
        }

        result = compiled.invoke(initial_state)

        final_output = result.get("final_output")
        if final_output:
            output = TriageOutput(**final_output)
            elapsed = int(time.time() * 1000) - start_ms
            output.processing_time_ms = elapsed
            logger.info(f"Pipeline complete: intent={output.intent}, urgency={output.urgency}, "
                       f"escalate={output.escalate}, time={elapsed}ms")
            return output
        else:
            logger.error("Pipeline produced no final_output")
            fb = safe_fallback_output(message_id, raw_input)
            fb.processing_time_ms = int(time.time() * 1000) - start_ms
            return fb

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        fb = safe_fallback_output(message_id, raw_input or "")
        fb.processing_time_ms = int(time.time() * 1000) - start_ms
        return fb
