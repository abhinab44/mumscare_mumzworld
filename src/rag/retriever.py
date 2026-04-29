from typing import List, Tuple
from loguru import logger
from src.rag.client import get_collection


def retrieve(query_text: str, n_results: int = 3) -> Tuple[List[str], List[float], bool]:
    """
    Query ChromaDB for relevant policy chunks.

    Returns:
        (chunks, scores, rag_grounded)
        - chunks: list of document text chunks
        - scores: list of similarity scores (1 - distance)
        - rag_grounded: True if at least one chunk scored > 0.4
    """
    try:
        collection = get_collection()
        if collection.count() == 0:
            logger.warning("ChromaDB collection is empty — not seeded")
            return [], [], False

        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection.count()),
            include=["documents", "distances", "metadatas"]
        )

        chunks = results["documents"][0] if results["documents"] else []
        distances = results["distances"][0] if results["distances"] else []

        # Convert cosine distance to similarity score
        scores = [round(1.0 - d, 4) for d in distances]

        # Grounding check: at least one chunk > 0.4 similarity
        rag_grounded = any(s > 0.4 for s in scores)

        logger.info(f"RAG retrieved {len(chunks)} chunks, grounded={rag_grounded}, top_score={scores[0] if scores else 0}")
        return chunks, scores, rag_grounded

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return [], [], False
