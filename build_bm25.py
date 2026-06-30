"""
build_bm25.py
One-time script to build and cache the BM25 index.
Run this after every ingestion/embedding update.
"""

from src.ingestion.loader import load_all_pdfs
from src.ingestion.chunker import chunk_documents
from src.retrieval.bm25 import build_bm25_index


if __name__ == "__main__":
    pages = load_all_pdfs("data/pdfs/cybersecurity")
    chunks = chunk_documents(pages)
    build_bm25_index(chunks)