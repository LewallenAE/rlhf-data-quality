import logging
import re
from .base import BaseSignal
from src.models import PreferenceRow

logger = logging.getLogger(__name__)



class RepetitionSignal(BaseSignal):
    def __init__(self, min_repeats: int = 3) -> None:
        self.min_repeats = min_repeats
        self.pattern = r'\b(\w+)(\s+\1){2,}\b'
        
    

    def analyze(self, rows: list[PreferenceRow]) -> list[dict]:
        signals = []
        
        logger.info(f"Analyzing {len(rows)} rows for repetition")

        for row in rows:
            for field in ['chosen', 'rejected']:
                text = getattr(row, field, "")
                if not text:
                    continue

                matches = re.findall(self.pattern, text.lower())

                if matches:
                    matched_words = [m[0] for m in matches]

                    signals.append({
                        "row_id": row.row_id,
                        "field": field,
                        "matched_pattern": matched_words,
                        "flagged": True
                    })
        return signals
