"""
embedder.py
Embeds chunks using Ollama and stores them in ChromaDB.
"""

import logging
import chromadb
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBED_MODEL = "nomic-embed-text"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "aria_cybersecurity"


def get_embedding(text: str) -> list[float]:
    response = ollama.embed(model=EMBED_MODEL, input=text)
    return response["embeddings"][0]


def embed_and_store(chunks: list[dict]) -> None:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    total_chunks = len(chunks)
    logger.info(f"Embedding {total_chunks} chunks...")

    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk["text"])
            collection.upsert(
                ids=[chunk["metadata"]["chunk_id"]],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[chunk["metadata"]],
            )
            if (i + 1) % 20 == 0 or (i + 1) == total_chunks:
                logger.info(f"Embedded {i + 1}/{total_chunks}")
        except Exception as e:
            logger.error(f"Failed chunk {chunk['metadata']['chunk_id']}: {e}")

    logger.info(f"Done. Collection now contains {collection.count()} chunks.")


if __name__ == "__main__":
    from src.ingestion.loader import load_all_pdfs
    from src.ingestion.chunker import chunk_documents
    pages = load_all_pdfs("data/pdfs/cybersecurity")
    chunks = chunk_documents(pages)
    embed_and_store(chunks)