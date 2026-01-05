import logging
from .base import BaseSignal
from src.models import PreferenceRow

logger = logging.getLogger(__name__)
REFUSAL_PHRASES = [
    "i can't help",
    "i cannot help",
    "i'm not able to",
    "i am not able to",
    "i won't be able to",
    "i'm unable to",
    "i cannot provide",
    "i will not provide",
    "i will not help",
    "i must decline",
    "i cannot assist",
    "i will not assist",
]

class RefusalBiasSignal(BaseSignal):
    def __init__(self):
        pass

    def _is_refusal(self, text:str) -> bool:
        if not text:
            return False
        return any (phrase in text.lower() for phrase in REFUSAL_PHRASES)

    def analyze(self, rows: list[PreferenceRow]) -> list[dict]:
        logger.info(f"Analyzing {len(rows)} rows for refusal bias.")
        results = []

        for row in rows:
            chosen_is_refusal = self._is_refusal(row.chosen)
            rejected_is_refusal = self._is_refusal(row.rejected)

            if chosen_is_refusal and not rejected_is_refusal:
                results.append({
                    "row_id": row.row_id,
                    "signal": "refusal_bias",
                    "reason": "Model preferred a refusal over a valid response",
                    "flagged":True
                })
        
        return results
        
        