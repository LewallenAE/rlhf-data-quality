from dataclasses import dataclass

@dataclass
class PreferenceRow:
    prompt: str
    chosen: str
    rejected: str
    row_id: str

    def __post_init__ (self):
        if not self.row_id:
            raise ValueError(f"Row_id is empty")
        elif not self.prompt:
            raise ValueError(f"Prompt is missing for row: {self.row_id}")
        elif not self.chosen:
            raise ValueError(f"Chosen is missing for row: {self.row_id}")
        elif not self.rejected:
            raise ValueError(f"Rejected is missing for row: {self.row_id}")
