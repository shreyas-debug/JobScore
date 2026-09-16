from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_model: Any = None


def _get_model() -> Any:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from app.core.config import settings
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model


def encode(text: str) -> list[float]:
    """Encode text into a 384-dim embedding vector.

    Raises TimeoutError on timeout so callers can fall back gracefully.
    Raises RuntimeError on any other model error.
    """
    model = _get_model()
    try:
        result = model.encode(text, normalize_embeddings=True)
        return result.tolist()
    except TimeoutError:
        logger.warning("Embedding encode timed out for text length=%d", len(text))
        raise
    except Exception as exc:
        logger.error("Embedding encode failed: %s", exc)
        raise RuntimeError("Embedding failed") from exc
