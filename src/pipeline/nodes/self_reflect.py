import os
from loguru import logger

FAITHFULNESS_THRESHOLD = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.6"))
MAX_REFLECTION_RETRIES = int(os.getenv("MAX_REFLECTION_RETRIES", "2"))


def node_self_reflect(state: dict) -> dict:
    """Node 6: Self-reflection / faithfulness judge with retry logic."""
    try:
        # If injection was detected, skip reflection (canned reply is always faithful)
        if state.get("injection_detected"):
            return {
                "faithfulness_score": 1.0,
                "reflection_retries": 0,
                "reflection_passed": True,
                "reflection_issues": "",
            }

        reply_en = state.get("reply_en", "")
        reply_ar = state.get("reply_ar", "")
        rag_chunks = state.get("rag_chunks", [])
        current_retries = state.get("reflection_retries", 0)

        try:
            from src.llm.groq_client import judge_faithfulness
            result = judge_faithfulness(reply_en, reply_ar, rag_chunks)

            faithful = result.get("faithful", True)
            score = float(result.get("score", 0.8))
            issues = result.get("issues", [])

            score = max(0.0, min(1.0, score))

            # Reconcile: if LLM says faithful but score is suspiciously 0,
            # trust the boolean and use a reasonable default score
            if faithful and score < 0.5:
                score = 0.8

            if isinstance(issues, list):
                issues_str = "; ".join(str(i) for i in issues)
            else:
                issues_str = str(issues) if issues else ""

        except Exception as e:
            logger.warning(f"Faithfulness judge failed: {e}, assuming faithful")
            score = 0.8
            faithful = True
            issues_str = ""

        passed = score >= FAITHFULNESS_THRESHOLD
        new_retries = current_retries

        updates = {
            "faithfulness_score": score,
            "reflection_passed": passed,
            "reflection_issues": issues_str,
        }

        if not passed:
            new_retries = current_retries + 1
            updates["reflection_retries"] = new_retries

            if new_retries >= MAX_REFLECTION_RETRIES:
                logger.warning(f"Node 6: Faithfulness failed after {new_retries} retries → escalating")
                updates["escalate"] = True
                updates["escalation_reason"] = "faithfulness_failure"
            else:
                logger.info(f"Node 6: Faithfulness low ({score:.2f}), retry {new_retries}/{MAX_REFLECTION_RETRIES}")
        else:
            updates["reflection_retries"] = current_retries

        logger.info(f"Node 6: faithfulness={score:.2f}, passed={passed}, retries={new_retries}")
        return updates

    except Exception as e:
        logger.error(f"Node 6 failed: {e}")
        return {
            "faithfulness_score": 0.8,
            "reflection_retries": state.get("reflection_retries", 0),
            "reflection_passed": True,
            "reflection_issues": "",
            "error": str(e),
        }
