"""
chunker.py
Splits page-level documents into smaller overlapping chunks.
"""

import logging
import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def generate_chunk_id(
    source: str,
    page: int,
    chunk_index: int,
    text: str,
) -> str:
    """
    Generate stable chunk IDs.
    """

    content = f"{source}_{page}_{chunk_index}_{text[:100]}"

    return hashlib.md5(content.encode()).hexdigest()


def chunk_documents(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Convert page-level documents into chunks.

    Input:
    {
        "text": "...",
        "metadata": {
            "source": "...",
            "page": ...
        }
    }

    Output:
    {
        "text": "...",
        "metadata": {
            "source": "...",
            "page": ...,
            "chunk_id": "...",
            "chunk_index": ...
        }
    }
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = []

    for page in pages:

        source = page["metadata"]["source"]
        page_number = page["metadata"]["page"]

        page_chunks = splitter.split_text(page["text"])

        logger.info(
            f"{source} | Page {page_number} → {len(page_chunks)} chunks"
        )

        for i, chunk_text in enumerate(page_chunks):

            chunk_id = generate_chunk_id(
                source=source,
                page=page_number,
                chunk_index=i,
                text=chunk_text,
            )

            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        "source": source,
                        "page": page_number,
                        "chunk_id": chunk_id,
                        "chunk_index": i,
                    },
                }
            )

    logger.info(f"Total chunks created: {len(chunks)}")

    return chunks


if __name__ == "__main__":

    from src.ingestion.loader import load_all_pdfs

    pages = load_all_pdfs("data/pdfs/cybersecurity")

    chunks = chunk_documents(pages)

    print(f"\nPages: {len(pages)}")
    print(f"Chunks: {len(chunks)}")

    if chunks:

        print("\nSample Chunk:\n")

        print(f"Chunk ID: {chunks[0]['metadata']['chunk_id']}")
        print(f"Source: {chunks[0]['metadata']['source']}")
        print(f"Page: {chunks[0]['metadata']['page']}")
        print(f"Chunk Index: {chunks[0]['metadata']['chunk_index']}")

        print("\nText Preview:\n")
        print(chunks[0]["text"][:300])