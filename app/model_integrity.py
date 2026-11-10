"""Integrity verification for locally loaded machine-learning models."""

import hashlib
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model_integrity(path: Path) -> None:
    """Verify a model against PEST_MODEL_SHA256 when configured."""
    expected = os.getenv("PEST_MODEL_SHA256", "").strip().lower()
    if not expected:
        if os.getenv("FLASK_ENV", "").lower() == "production":
            raise RuntimeError(
                "PEST_MODEL_SHA256 must be configured before loading a production model."
            )
        logger.warning(
            "PEST_MODEL_SHA256 is not configured; model integrity verification is disabled."
        )
        return

    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ValueError("PEST_MODEL_SHA256 must be a 64-character hexadecimal SHA-256 digest.")

    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(
            f"Model integrity verification failed for {path.name}: "
            f"expected {expected}, calculated {actual}."
        )
