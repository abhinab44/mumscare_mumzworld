# ARCHITECTURE.md — MomCare Pipeline Design

## System Overview

```
User Query (EN/AR)
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                      │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │  Node 1  │──▶│  Node 2  │──▶│  Node 3  │               │
│  │  Detect  │   │  Intent  │   │ Urgency  │               │
│  │ Normalize│   │ Classify │   │  Score   │               │
│  └──────────┘   └──────────┘   └──────────┘               │
│                                      │                      │
│                                      ▼                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │  Node 7  │◀──│  Node 6  │◀──│  Node 4  │               │
│  │ Pydantic │   │  Self-   │   │   RAG    │               │
│  │ Validate │   │ Reflect  │   │ Retrieve │               │
│  └──────────┘   └──────────┘   └──────────┘               │
│        ▲                             │                      │
│        │                             ▼                      │
│        │                        ┌──────────┐               │
│        └────────────────────────│  Node 5  │               │
│                                 │  Reply   │               │
│                                 │ Generate │               │
│                                 └──────────┘               │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
 TriageOutput (Pydantic-validated JSON)
      │
      ▼
 Streamlit UI (chat card + JSON panel)
```

---

## LangGraph State

```python
class AgentState(TypedDict):
    # Input
    raw_input: str
    message_id: str
    
    # Node 1 outputs
    detected_language: str        # "en" | "ar"
    normalized_text: str
    lang_confidence: float
    
    # Node 2 outputs
    intent: str
    intent_confidence: float
    
    # Node 3 outputs
    urgency: str                  # "low"|"medium"|"high"|"critical"
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
    
    # Node 7 outputs
    final_output: Optional[TriageOutput]
    schema_valid: bool
    
    # Cross-cutting
    escalate: bool
    escalation_reason: Optional[str]
    error: Optional[str]
```

---

## Node Specifications

### Node 1: Language Detection + Normalization
**Input**: `raw_input`  
**Libraries**: `langdetect`, `re`, `html`  
**Logic**:
1. Strip HTML entities (`html.unescape`)
2. Truncate to 2000 chars
3. `langdetect.detect_langs()` → top language + probability
4. If Arabic Unicode range (`\u0600-\u06FF`) > 30% of chars → force `ar`
5. If confidence < 0.6 → default `en`, log warning
6. Normalize whitespace, remove null bytes

**Fallback**: any exception → `detected_language="en"`, `normalized_text=raw_input[:500]`

---

### Node 2: Intent Classification
**Input**: `normalized_text`, `detected_language`  
**Model**: Groq `llama3-8b-8192` (temperature=0.1)  
**Prompt**: structured few-shot with 7 class definitions (see PROMPTS.md)  
**Output**: JSON `{"intent": "...", "confidence": 0.0–1.0}`  
**Fallback**: regex keyword matching (order→`order_status`, return→`return_refund`, etc.)

**Intent → Escalation pre-check**:
- `medical_concern` → set `urgency` floor = `high`
- Confidence < 0.55 → `general_inquiry` + `escalate=True` flag

---

### Node 3: Urgency Scoring
**Input**: `normalized_text`, `intent`  
**Logic** (layered):

Layer 1 — Keyword rules (instant `critical`):
```
["allergic reaction", "can't breathe", "emergency", "bleeding", 
 "fell down", "swallowed", "unconscious", "حساسية شديدة", "طوارئ"]
```

Layer 2 — LLM scoring (temperature=0.1):
- Returns float 0.0–1.0
- Mapped: <0.3→low, 0.3–0.6→medium, 0.6–0.85→high, >0.85→critical

Layer 3 — Safety override:
- `intent=medical_concern` → minimum `high`
- `urgency=critical` → `escalate=True`, `escalation_reason="safety"`

---

### Node 4: RAG Retrieval (ChromaDB)
**Input**: `normalized_text`  
**Setup**:
```python
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="mumzworld_policies",
    embedding_function=SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
)
```
**Query**: top-3 chunks, cosine distance  
**Grounding check**: if all scores < 0.4 → `rag_grounded=False`  
**Policy corpus** (5 synthetic docs, see CONTEXT.md):
- Return & Refund Policy
- Delivery & Shipping FAQ
- Product Safety Guidelines
- Account & Wallet Help
- Medical Disclaimer + Escalation Policy

---

### Node 5: Reply Generation
**Input**: `normalized_text`, `detected_language`, `intent`, `urgency`, `rag_chunks`, `rag_grounded`  
**Model**: Groq `llama3-70b-8192` (temperature=0.7)  
**Always generates both** `reply_en` and `reply_ar`  
**Arabic constraints** (enforced in prompt):
- Gulf dialect (UAE/KSA)
- Empathetic openers: "يا حياتي", "أهلاً وسهلاً"
- No literal EN→AR translation
- Uncertainty hedge if `rag_grounded=False`: "سأحوّلك لفريقنا المختص"

---

### Node 6: Self-Reflection
**Input**: `reply_en`, `reply_ar`, `rag_chunks`, `faithfulness_score`, `reflection_retries`  
**Model**: Groq `llama3-8b-8192` (temperature=0.0) — deterministic judge  
**Prompt**: "Does this reply contradict or hallucinate beyond these policy chunks? Return JSON {faithful: bool, score: 0.0-1.0, issues: []}"  

**Retry logic**:
```
if faithfulness_score < 0.6 and reflection_retries < 2:
    → re-invoke Node 5 with stricter prompt ("only use provided context")
    → increment reflection_retries
elif faithfulness_score < 0.6 and reflection_retries >= 2:
    → escalate = True, escalation_reason = "faithfulness_failure"
    → use safe_fallback_reply()
```

---

### Node 7: Pydantic Schema Validation
**Input**: entire `AgentState`  
**Action**: construct `TriageOutput(**state)`, validate  
**On failure**:
- Log field errors
- Set `schema_valid=False`
- Replace with `SafeFallbackOutput` (pre-built static safe response)
- Never propagate partial/invalid output

---

## Graph Edges

```python
graph.add_edge(START, "detect_normalize")
graph.add_edge("detect_normalize", "classify_intent")
graph.add_edge("classify_intent", "score_urgency")
graph.add_edge("score_urgency", "rag_retrieve")
graph.add_edge("rag_retrieve", "generate_reply")
graph.add_edge("generate_reply", "self_reflect")

# Conditional edge on reflection
graph.add_conditional_edges(
    "self_reflect",
    lambda s: "generate_reply" if (s["faithfulness_score"] < 0.6 and s["reflection_retries"] < 2) else "validate_schema",
    {"generate_reply": "generate_reply", "validate_schema": "validate_schema"}
)

graph.add_edge("validate_schema", END)
```

---

## Failure Modes + Mitigations

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| LLM timeout | try/except + 10s timeout | Fallback to keyword rules |
| ChromaDB not seeded | Collection empty check | Return grounded=False, hedge reply |
| Arabic garbled | Unicode validation | Fallback to EN-only with note |
| Faithfulness loop | retry counter | Hard cap at 2, escalate |
| Schema mismatch | Pydantic ValidationError | SafeFallbackOutput |
| Prompt injection | Input sanitization | Detect + refuse (see SECURITY.md) |
