import logging
from .base import BaseSignal
from src.models import PreferenceRow

logger = logging.getLogger(__name__)


UNSAFE_KEYWORDS = [
    #Violence
    "how to kill",
    "how to murder",
    "how to hurt",
    "how to attack",

    # Weapons
    "how to make a bomb",
    "how to make a weapon",
    "how to buy a gun illegally",

    # Illegal
    "how to hack",
    "how to steal",
    "how to break into",
    "how to smuggle",
    "how to avoid law enforcement",

    # Self-Harm
    "how to commit suicide",
    "ways to kill myself",
    "how to self-harm",
]

class UnsafePromptSignal(BaseSignal):

    def __init__(self):
        pass
    
    def _find_unsafe_keyword(self, text: str) -> str | None:
        text_lower = text.lower()
        for keyword in UNSAFE_KEYWORDS:
            if keyword in text_lower:
                return keyword
        return None

    def analyze(self, rows: list[PreferenceRow]) -> list[dict]:
        logger.info(f"Analyzing {len(rows)} in rows for unsafe prompts")
        results = []

        for row in rows:
            keyword = self._find_unsafe_keyword(row.prompt)

            if keyword is not None:
                results.append({
                    "row_id": row.row_id,
                    "matched_keyword": keyword,
                    "flagged": True
                })
        return results