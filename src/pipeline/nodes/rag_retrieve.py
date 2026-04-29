from loguru import logger


def node_rag_retrieve(state: dict) -> dict:
    """Node 4: RAG retrieval from ChromaDB."""
    try:
        # If injection was detected, skip RAG
        if state.get("injection_detected"):
            return {
                "rag_chunks": [],
                "rag_scores": [],
                "rag_grounded": False,
            }

        normalized_text = state.get("normalized_text", "")

        from src.rag.retriever import retrieve
        chunks, scores, rag_grounded = retrieve(normalized_text, n_results=3)

        logger.info(f"Node 4: retrieved {len(chunks)} chunks, grounded={rag_grounded}")

        return {
            "rag_chunks": chunks,
            "rag_scores": scores,
            "rag_grounded": rag_grounded,
        }

    except Exception as e:
        logger.error(f"Node 4 failed: {e}")
        return {
            "rag_chunks": [],
            "rag_scores": [],
            "rag_grounded": False,
            "error": str(e),
        }
