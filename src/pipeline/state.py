from typing import TypedDict, Optional, List


class AgentState(TypedDict):
    # Input
    raw_input: str
    message_id: str

    # Node 1 outputs
    detected_language: str          # "en" | "ar"
    lang_confidence: float
    normalized_text: str
    injection_detected: bool

    # Node 2 outputs
    intent: str
    intent_confidence: float

    # Node 3 outputs
    urgency: str                    # "low" | "medium" | "high" | "critical"
    urgency_score: float

    # Node 4 outputs
    rag_chunks: List[str]
    rag_scores: List[float]
    rag_grounded: bool

    # Node 5 outputs
    reply_en: str
    reply_ar: str

    # Node 6 outputs
    faithfulness_score: float
    reflection_retries: int
    reflection_passed: bool
    reflection_issues: str

    # Node 7 outputs
    final_output: Optional[dict]
    schema_valid: bool

    # Cross-cutting
    escalate: bool
    escalation_reason: Optional[str]
    error: Optional[str]
    processing_start_ms: int
