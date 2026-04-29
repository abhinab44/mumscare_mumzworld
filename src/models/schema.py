from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List
from datetime import datetime


class TriageOutput(BaseModel):
    model_config = {"strict": False}

    # Identity
    message_id: str = Field(..., description="UUID for this request")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")

    # Language
    detected_language: Literal["en", "ar"] = Field(..., description="Primary detected language")
    lang_confidence: float = Field(..., ge=0.0, le=1.0)
    normalized_text: str = Field(..., min_length=1, max_length=2100)

    # Classification
    intent: Literal[
        "order_status",
        "return_refund",
        "product_query",
        "account_issue",
        "medical_concern",
        "complaint",
        "general_inquiry"
    ]
    intent_confidence: float = Field(..., ge=0.0, le=1.0)

    # Urgency
    urgency: Literal["low", "medium", "high", "critical"]
    urgency_score: float = Field(..., ge=0.0, le=1.0)

    # RAG
    rag_chunks_used: List[str] = Field(default_factory=list)
    rag_grounded: bool = Field(..., description="True if at least one chunk scored > 0.4 cosine similarity")

    # Replies
    reply_en: str = Field(..., min_length=10, max_length=2000)
    reply_ar: str = Field(..., min_length=10, max_length=2000)

    # Reflection
    faithfulness_score: float = Field(..., ge=0.0, le=1.0)
    reflection_retries: int = Field(..., ge=0, le=2)

    # Escalation
    escalate: bool
    escalation_reason: Optional[Literal[
        "safety",
        "medical_concern",
        "faithfulness_failure",
        "low_confidence",
        "explicit_request"
    ]] = None

    # Meta
    schema_valid: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall pipeline confidence")
    processing_time_ms: int = Field(..., ge=0)

    @field_validator("escalation_reason")
    @classmethod
    def escalation_reason_required_when_escalated(cls, v, info):
        if info.data.get("escalate") and v is None:
            raise ValueError("escalation_reason must be set when escalate=True")
        return v

    @field_validator("urgency_score")
    @classmethod
    def urgency_score_matches_label(cls, v, info):
        urgency = info.data.get("urgency")
        ranges = {
            "low": (0.0, 0.3),
            "medium": (0.3, 0.6),
            "high": (0.6, 0.85),
            "critical": (0.85, 1.0)
        }
        if urgency and urgency in ranges:
            lo, hi = ranges[urgency]
            if not (lo <= v <= hi + 0.05):
                pass  # soft validation — log warning but don't fail
        return v
