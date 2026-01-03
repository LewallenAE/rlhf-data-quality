import logging
import textstat
from .base import BaseSignal
from src.models import PreferenceRow

logger = logging.getLogger(__name__)

class ReadabilityMismatchSignal(BaseSignal):
    def __init__(self, max_diff: float = 5.0) -> None:
        self.max_diff = max_diff
        self.score = textstat.flesch_kincaid_grade


    def analyze(self, rows: list[PreferenceRow]) -> list[dict]:
        logger.info(f"Analyzing {len(rows)} for rows in ReadabilityMismatchSignal")

        results = []

        for row in rows:
            chosen_score = self.score(row.chosen)
            rejected_score = self.score(row.rejected)

            diff = abs(chosen_score - rejected_score)

            if diff > self.max_diff:
                results.append({
                    "row_id": row.row_id,
                    "chosen_grade": chosen_score,
                    "rejected_grade": rejected_score,
                    "flagged": True
                })
        return results

