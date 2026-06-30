"""
loader.py
Extracts text from PDF files and preserves page-level metadata.
"""

import fitz  # PyMuPDF
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pages with these keywords are usually noise
REFERENCE_KEYWORDS = [
    "references",
    "bibliography",
    "appendix",
    "index",
    "glossary",
]

MIN_TEXT_LENGTH = 100


def is_reference_page(text: str) -> bool:
    """
    Detect reference pages using keywords.
    """
    text_lower = text.lower()

    return any(keyword in text_lower for keyword in REFERENCE_KEYWORDS)


def load_pdf(pdf_path: str) -> list[dict]:
    """
    Load a PDF and return page-level documents.

    Returns:
    [
        {
            "text": "...",
            "metadata": {
                "source": "...",
                "page": 1
            }
        }
    ]
    """

    pdf_path = Path(pdf_path)

    logger.info(f"Loading PDF: {pdf_path.name}")

    doc = fitz.open(pdf_path)

    pages = []

    for page_num, page in enumerate(doc, start=1):

        text = page.get_text().strip()

        # Skip empty pages
        if not text:
            continue

        # Skip tiny pages
        if len(text) < MIN_TEXT_LENGTH:
            continue

        # Skip references / appendix pages
        if is_reference_page(text):
            logger.info(f"Skipping reference page {page_num}")
            continue

        pages.append(
            {
                "text": text,
                "metadata": {
                    "source": pdf_path.name,
                    "page": page_num,
                },
            }
        )

    doc.close()

    logger.info(f"{len(pages)} pages extracted from {pdf_path.name}")

    return pages


def load_all_pdfs(folder_path: str) -> list[dict]:
    """
    Load all PDFs from a folder.
    """

    folder = Path(folder_path)

    all_pages = []

    for pdf_file in folder.glob("*.pdf"):

        pages = load_pdf(str(pdf_file))

        all_pages.extend(pages)

    logger.info(f"Total pages loaded: {len(all_pages)}")

    return all_pages


if __name__ == "__main__":

    docs = load_all_pdfs("data/pdfs/cybersecurity")

    print(f"\nLoaded {len(docs)} pages")

    if docs:

        print("\nSample Page:\n")

        print(f"Source: {docs[0]['metadata']['source']}")
        print(f"Page: {docs[0]['metadata']['page']}")
        print(docs[0]["text"][:300])