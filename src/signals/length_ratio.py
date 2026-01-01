import logging
from .base import BaseSignal
from src.models import PreferenceRow

logger = logging.getLogger(__name__)

class LengthRatioSignal(BaseSignal):
    def __init__(self, max_ratio: float = 3.0):
        self.max_ratio = max_ratio
    
    def analyze(self, rows: list[PreferenceRow]) -> list[dict]:
        logger.info(f"Analyzing {len(rows)} rows")
        results = []           
        
        for row in rows:

            if len(row.chosen) == 0 or len(row.rejected) == 0:
                results.append({
                    "row_id": row.row_id,
                    "ratio": None,
                    "flagged": True,
                })
                logger.warning(f"Empty response in row {row.row_id}")
                continue

            ratio = len(row.chosen) / len(row.rejected)

            if ratio > self.max_ratio or ratio < 1/self.max_ratio:
                results.append({
                "row_id": row.row_id,
                "ratio": ratio,
                "flagged": True,
                })
        
        return results
    