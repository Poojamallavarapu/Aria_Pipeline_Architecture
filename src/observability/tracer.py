"""
tracer.py
Langfuse client initialization, loaded once and reused across the app.
"""

import os
import logging
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

logger = logging.getLogger(__name__)

_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
# Fix: env file uses LANGFUSE_BASE_URL, not LANGFUSE_HOST
_host = os.getenv("LANGFUSE_BASE_URL", os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"))

if not _public_key or not _secret_key:
    logger.warning(
        "LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set. "
        "Tracing will be disabled or use default keys."
    )

langfuse = Langfuse(
    public_key=_public_key,
    secret_key=_secret_key,
    host=_host,
)