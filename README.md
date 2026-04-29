# MomCare — Multilingual Support Triage Agent

**Mumzworld AI-Native Internship · Track A · Abhinab Kashyap**

---

MomCare is a production-grade customer support triage agent built for Mumzworld — the largest baby and maternity e-commerce platform in the Middle East. It processes incoming customer queries in English and Gulf Arabic through a 7-node LangGraph pipeline that detects language, classifies intent (7 classes), scores urgency, retrieves grounding policy context via RAG (ChromaDB), generates bilingual empathetic replies in Gulf dialect, self-validates faithfulness with a retry loop, and produces a strict Pydantic-validated `TriageOutput` JSON. Safety-critical behaviors — medical query refusal, prompt injection blocking, and system prompt protection — are hard-coded overrides that never depend on LLM judgment.

---

## Prototype Access

**GitHub**: [https://github.com/abhinab44/mumscare_mumzworld](https://github.com/abhinab44/mumscare_mumzworld)

### Setup (under 5 minutes)

```bash
git clone https://github.com/abhinab44/mumscare_mumzworld.git
cd mumscare_mumzworld

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env → add your GROQ_API_KEY (free at console.groq.com)

# Seed the policy database (one-time)
python scripts/seed_chroma.py

# Launch
streamlit run src/ui/app.py
```

**→ Open http://localhost:8501**

---

## 3-Minute Walkthrough



---

## Architecture

7-node LangGraph StateGraph pipeline with conditional self-reflection retry:

```
Input → [1. Detect & Normalize] → [2. Classify Intent] → [3. Score Urgency] → [4. RAG Retrieve]
                                                                                       ↓
Output ← [7. Validate Schema] ← [6. Self-Reflect ↺] ← [5. Generate Reply]
```

| Node | Model | Function |
|------|-------|----------|
| 1. Detect & Normalize | `langdetect` + regex | Language ID (EN/AR), input sanitization, injection blocking |
| 2. Classify Intent | Llama 3.1 8B | 7-class classification with keyword fallback |
| 3. Score Urgency | Llama 3.1 8B | Keyword rules → LLM scoring → medical safety override |
| 4. RAG Retrieve | `all-MiniLM-L6-v2` + ChromaDB | Top-3 policy chunks, cosine similarity ≥ 0.40 |
| 5. Generate Reply | Llama 3.3 70B | Bilingual EN + AR (Gulf dialect) in single prompt |
| 6. Self-Reflect | Llama 3.1 8B | Faithfulness judge; retry ×2 if score < 0.6 |
| 7. Validate Schema | Pydantic v2 | `TriageOutput` validation; safe fallback on failure |

---

## Evaluation Results

13 test cases: 5 happy path · 5 edge cases · 3 adversarial.

```bash
# Run full eval suite
python scripts/run_full_eval.py

# Run core 5 demo cases
python scripts/validate_demo.py
```

### Aggregate Scores

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| **Overall Score** | ≥ 0.80 | **0.851** | ✅ |
| Intent Accuracy | ≥ 85% | **100%** (12/12) | ✅ |
| Schema Pass Rate | 100% | **100%** (13/13) | ✅ |
| Faithfulness Avg | ≥ 0.75 | 0.646 | ⚠️ Rate-limit noise |
| Escalation Accuracy | ≥ 90% | 83.3% | ⚠️ False positives from retry exhaustion |
| Medical Safety | 100% | **100%** | ✅ |
| Injection Blocking | 100% | **100%** | ✅ |

> **Note on faithfulness**: The 0.646 average is degraded by Groq free-tier rate limiting (30 req/min) during batch eval. In single-query mode, faithfulness consistently scores ≥ 0.80. The 2 false escalations (TC-03, TC-04) are caused by the faithfulness judge returning 0.0 under load — not by unsafe replies.

### Demo-Critical Cases (5/5 Pass)

| Test Case | Intent | Urgency | Safety | Status |
|-----------|--------|---------|--------|--------|
| Arabic Order Status | ✅ order_status | ✅ medium | — | ✅ |
| Refund Timeline | ✅ return_refund | ✅ medium | — | ✅ |
| Medical Emergency | ✅ medical_concern | ✅ critical | ✅ No meds, cites 998/911 | ✅ |
| RAG Miss (Discount) | ✅ general_inquiry | ✅ low | ✅ No hallucinated codes | ✅ |
| Prompt Injection | ✅ complaint | ✅ low | ✅ Blocked Node 1, 0ms | ✅ |

Full methodology, per-case results, and failure analysis: **[EVALS.md](EVALS.md)**

---

## Key Tradeoffs

| Decision | Chose | Over | Why |
|----------|-------|------|-----|
| Inference | Groq (cloud, <1s) | Ollama (local, ~60s) | Latency matters for support; rate limits accepted |
| Classification | Llama 3.1 8B | Llama 3.3 70B | Sufficient for 7-class JSON; saves rate budget |
| Generation | Llama 3.3 70B | Llama 3.1 8B | 70B follows Gulf dialect instructions reliably |
| Vector DB | ChromaDB (local) | Pinecone (cloud) | Zero infra, free, adequate for 8-doc corpus |
| Bilingual | Single-prompt EN+AR | Translate after | Gulf dialect phrases don't survive translation |
| UI | Streamlit | FastAPI + React | 90-min build vs 4+ hours; demo-appropriate |
| Safety | Hard-coded overrides | LLM-dependent | Medical/injection rules must never rely on LLM judgment |

Full decision log with measured data: **[TRADEOFFS.md](TRADEOFFS.md)**

---

## Tooling & AI Usage

### Harnesses and Models Used

| Tool / Model | Role | How Used |
|--------------|------|----------|
| **Groq API** + `llama-3.1-8b-instant` | Production classifier, urgency scorer, faithfulness judge | Core pipeline inference — called via `httpx` in `groq_client.py`. Chosen for sub-1s JSON-mode responses. |
| **Groq API** + `llama-3.3-70b-versatile` | Production reply generator | Bilingual EN+AR generation in a single prompt. 70B chosen over 8B because it follows Gulf Arabic dialect instructions more reliably. |
| **OpenRouter** + `llama-3.3-70b` | Fallback inference | Activated when Groq returns 429/503. Same model, different provider, separate rate pool. |
| **GitHub Copilot** (VS Code) | Inline autocomplete | Tab-completion for repetitive patterns: Pydantic field definitions, test case JSON scaffolding, `httpx` boilerplate. |
| **ChromaDB** + `all-MiniLM-L6-v2` | Embedding + retrieval | Local vector store for 8 policy documents. Sentence-transformers model used via ChromaDB's default embedding function. |

### How I Used Them

- **Pair-coding with Copilot**: Used inline suggestions for mechanical tasks — filling out the 13 test case JSON structures in `sample_data/`, writing repetitive node function signatures, and auto-completing Pydantic validators. Accepted ~60% of suggestions; rejected the rest when they assumed wrong field names or hallucinated API signatures.
- **One-shot generation**: The initial `groq_client.py` HTTP wrapper was written in one pass with Copilot suggesting the `httpx.post` call structure. I then manually added retry logic, rate-limit handling, and the `_extract_json_regex` fallback for malformed responses.
- **Prompt iteration (manual)**: All LLM system prompts were written and iterated by hand. The Arabic dialect prompt went through 4 revisions — Copilot has no useful opinion on Gulf vs. MSA Arabic phrasing. The key system message for reply generation:

```
You are Maya, Mumzworld's AI support assistant.
Respond in GULF ARABIC dialect (UAE/KSA), not Modern Standard Arabic.
Use: أهلاً وسهلاً, يا حياتي, بإذن الله, سنساعدك حالاً, إن شاء الله
Never use: سيدتي الفاضلة, نود إعلامكم (too formal/MSA)
```

- **Eval grading**: The faithfulness judge prompt was written manually and tested against known-good and known-bad replies before integration. The scoring formula in `EVALS.md` was designed by hand to weight safety (escalation) higher than convenience (urgency accuracy).

### What Worked

- **Groq's JSON mode** (`response_format: {"type": "json_object"}`) eliminated 90% of parsing failures. Without it, the 8B model returns free-form text ~30% of the time.
- **Copilot for boilerplate**: Saved ~30 minutes on test case JSON and Pydantic model definitions. Good at pattern replication, bad at novel logic.
- **Separate models for classification vs. generation**: 8B for fast classification (0.6–1.5s), 70B for quality generation (1.5–3s). This split keeps total pipeline latency under 10s for most cases while maintaining Arabic quality.

### What Didn't Work

- **Copilot on Arabic prompts**: Suggested MSA-style phrases ("سيدتي الفاضلة") that sound corporate and cold. Gulf dialect requires hand-crafted examples — no AI tool got this right without explicit overriding.
- **Faithfulness judge under rate limits**: The 8B judge returns `{"faithful": false, "score": 0.0}` when Groq is rate-limited (429). This is not a genuine assessment — it's the model producing garbage under degraded conditions. I added reconciliation logic (`if faithful==true and score<0.5 → default to 0.8`) but the `faithful=false` case remains unaddressed without upgrading to a paid tier.
- **Copilot on LangGraph**: Suggested `SequentialChain` (LangChain, not LangGraph) and `StateGraph` constructor args that don't exist. All LangGraph wiring in `graph.py` was written from the docs, not from AI suggestions.

### Where I Overruled the Agent

1. **Medical safety override**: Copilot suggested routing medical queries through the standard LLM generation path with a "be careful" system prompt addition. I rejected this and hard-coded a template response with emergency numbers (UAE: 998, KSA: 911) that bypasses the LLM entirely. Safety-critical paths must not depend on LLM compliance.
2. **Urgency thresholds**: Copilot suggested equal-width buckets (0–0.25, 0.25–0.50, 0.50–0.75, 0.75–1.0). I used asymmetric thresholds (low: 0–0.29, medium: 0.30–0.64, high: 0.65–0.84, critical: 0.85+) calibrated against the actual LLM score distribution from test runs.
3. **ChromaDB PersistentClient**: Copilot suggested `chromadb.Client()` (ephemeral — data lost on restart). Corrected to `PersistentClient(path="./chroma_db")` from the ChromaDB docs.
4. **Injection detection**: Copilot suggested an LLM-based classifier for injection detection. I used regex patterns instead — `"ignore.*instructions"`, `"you are now"`, `"no restrictions"` — because injection detection must be deterministic and zero-latency (0ms vs. 1–2s for an LLM call).

### Key Config That Shaped Output

```python
# .env — tuned during eval runs
FAITHFULNESS_THRESHOLD=0.6    # Below this → retry generation
MAX_REFLECTION_RETRIES=2      # After 2 failures → escalate to human
LLM_TIMEOUT_SECONDS=30        # Groq free tier needs headroom for 70B

# groq_client.py — retry strategy for 30 req/min free tier
max_attempts = 3
retry_after = min(int(resp.headers.get("retry-after", "3")), 10)
```

---


## Time Log

| Phase | Time |
|-------|------|
| Problem selection + architecture design | ~45 min |
| LangGraph pipeline (7 nodes + state management) | ~90 min |
| RAG integration (ChromaDB seeding, retriever, grounding logic) | ~45 min |
| Prompt engineering (Arabic dialect iteration, safety prompts) | ~60 min |
| Streamlit UI + eval suite + documentation | ~90 min |
| **Total** | **~5.5 hours** (went slightly over due to Arabic quality iteration) |

---

## Project Structure

```
momcare/
├── src/
│   ├── pipeline/
│   │   ├── graph.py              # LangGraph StateGraph + run_triage()
│   │   ├── state.py              # AgentState TypedDict
│   │   └── nodes/                # 7 pipeline nodes
│   ├── llm/
│   │   └── groq_client.py        # Groq API client (classify, score, generate, judge)
│   ├── rag/
│   │   ├── client.py             # ChromaDB PersistentClient
│   │   └── retriever.py          # Semantic search + grounding logic
│   ├── models/
│   │   ├── schema.py             # TriageOutput Pydantic model
│   │   └── fallback.py           # Safe fallback outputs
│   └── ui/
│       └── app.py                # Streamlit application
├── scripts/
│   ├── seed_chroma.py            # One-time policy database seeder
│   ├── run_full_eval.py          # Full 13-case eval suite
│   └── validate_demo.py          # Core 5-case demo validation
├── sample_data/                  # Test cases (happy_path, edge_cases, adversarial)
├── chroma_db/                    # Persistent vector store (auto-created)
├── EVALS.md                      # Evaluation framework + results
├── TRADEOFFS.md                  # Architectural decision log
├── ARCHITECTURE.md               # System design documentation
├── SECURITY.md                   # Threat model + mitigations
├── PROMPTS.md                    # LLM prompt templates
├── requirements.txt
└── .env.example
```
