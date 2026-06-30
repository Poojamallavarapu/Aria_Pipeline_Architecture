"""
vector.py
Retrieves relevant chunks from ChromaDB.
"""

import logging
import chromadb

from src.ingestion.embedder import (
    get_embedding,
    CHROMA_PATH,
    COLLECTION_NAME,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks.
    """

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    retrieved = []

    for i in range(len(results["ids"][0])):

        retrieved.append(
            {
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )

    return retrieved


if __name__ == "__main__":

    query = input("Query: ")

    results = retrieve(query)

    print("\n===== RETRIEVED RESULTS =====\n")

    for i, result in enumerate(results, start=1):

        print(f"Result {i}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Source: {result['metadata']['source']}")
        print(f"Page: {result['metadata']['page']}")

        print("\nText Preview:")
        print(result["text"][:300])

        print("-" * 80)