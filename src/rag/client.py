import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

_client = None
_collection = None


def get_collection():
    """Get or create the ChromaDB collection with sentence-transformer embeddings."""
    global _client, _collection
    if _collection is not None:
        return _collection

    logger.info(f"Connecting to ChromaDB at {CHROMA_DB_PATH}")
    _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    _collection = _client.get_or_create_collection(
        name="mumzworld_policies",
        metadata={"hnsw:space": "cosine"},
        embedding_function=embedding_fn,
    )
    logger.info(f"Collection 'mumzworld_policies' ready, {_collection.count()} documents")
    return _collection


def is_seeded() -> bool:
    """Check if the ChromaDB collection has been seeded."""
    try:
        col = get_collection()
        return col.count() > 0
    except Exception:
        return False
