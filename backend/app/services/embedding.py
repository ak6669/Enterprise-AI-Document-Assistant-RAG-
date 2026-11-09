import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Local embedding service leveraging Sentence Transformers.
    Generates fast, normalized dense vectors without external API calls or latency.
    """

    _instance = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if self._model is None:
            self.model_name = model_name
            self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model '{self.model_name}': {e}")
            raise

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates normalized vector embeddings for a list of text strings."""
        if not texts:
            return []
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Generates a single normalized vector embedding for a query string."""
        clean_query = query.strip()
        if not clean_query:
            return []
        embedding = self._model.encode(
            clean_query,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embedding.tolist()
