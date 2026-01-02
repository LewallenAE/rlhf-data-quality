import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from .base import BaseSignal
from src.models import PreferenceRow

logger = logging.getLogger(__name__)

class SemanticDuplicateSignal(BaseSignal):
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def analyze(self, rows: list[PreferenceRow]) -> list[dict]:
        logger.info(f"Analyzing {len(rows)} rows for semantic duplicates")

        texts = [row.chosen for row in rows]

        embeddings = self.model.encode(texts)
        results = []

        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = self._cosine_similarity(embeddings[i], embeddings[j])
                if sim > self.threshold:
                    results.append({
                        "row_id_1": rows[i].row_id,
                        "row_id_2": rows[j].row_id,
                        "similarity": float(sim),
                        "flagged": True
                    })
        logger.info(f"Found {len(results)} duplicate pairs")
        return results
    
    def _cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
