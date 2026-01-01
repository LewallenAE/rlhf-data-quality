from abc import ABC, abstractmethod
from src.models import PreferenceRow

class BaseSignal(ABC):
    @abstractmethod
    def analyze(self, rows: list[PreferenceRow]) -> list[dict]:
        pass
    