"""
embedder.py
Embeds chunks using Ollama and stores them in ChromaDB.
Includes retry logic and text truncation to handle Ollama disconnects.
"""

import logging
import time
import chromadb
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBED_MODEL = "nomic-embed-text"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "aria_cybersecurity"
MAX_CHARS = 2000   # truncate chunks longer than this before embedding
RETRY_LIMIT = 3
RETRY_DELAY = 2    # seconds between retries


def get_embedding(text: str) -> list[float] | None:
    # Truncate if too long — prevents Ollama timeout on huge chunks
    text = text[:MAX_CHARS].strip()
    if not text:
        return None

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            response = ollama.embed(model=EMBED_MODEL, input=text)
            return response["embeddings"][0]
        except Exception as e:
            logger.warning(f"  Attempt {attempt}/{RETRY_LIMIT} failed: {e}")
            if attempt < RETRY_LIMIT:
                time.sleep(RETRY_DELAY)

    logger.error(f"  All {RETRY_LIMIT} attempts failed — skipping this chunk.")
    return None


def embed_and_store(chunks: list[dict]) -> None:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    total_chunks = len(chunks)
    skipped = 0
    logger.info(f"Embedding {total_chunks} chunks...")

    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk["text"])

            if embedding is None:
                skipped += 1
                continue

            collection.upsert(
                ids=[chunk["metadata"]["chunk_id"]],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[chunk["metadata"]],
            )

            # Small pause every 10 chunks to avoid overwhelming Ollama
            if (i + 1) % 10 == 0:
                time.sleep(0.3)

            if (i + 1) % 20 == 0 or (i + 1) == total_chunks:
                logger.info(f"  Embedded {i + 1}/{total_chunks} | Skipped so far: {skipped}")

        except Exception as e:
            logger.error(f"Failed chunk {chunk['metadata']['chunk_id']}: {e}")
            skipped += 1

    logger.info(f"Done. Collection contains {collection.count()} chunks. Skipped: {skipped}/{total_chunks}")


if __name__ == "__main__":
    from src.ingestion.loader import load_all_pdfs
    from src.ingestion.chunker import chunk_documents
    pages = load_all_pdfs("data/pdfs/cybersecurity")
    chunks = chunk_documents(pages)
    embed_and_store(chunks)