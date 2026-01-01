from datasets import load_dataset
from src.models import PreferenceRow

def parse_conversation(conversation:str) -> tuple[str, str]:
    """
    Parse an HH-RLHF conversation string into (prompt, response).

    Returns:
        tuple of (prompt, response)
    
    """


    parts = conversation.rsplit("\n\nAssistant: ", maxsplit=1)

    if len(parts) != 2:
        raise ValueError(f"Invalid format, expected length of 2, got {len(parts)}")
    
    prompt = parts[0].strip().removeprefix("Human: ").strip()
    response = parts[1]

    return prompt, response


class HHRLHFLoader:
    def __init__(self, split: str = "train", limit: int | None = None):
        self.split = split
        self.limit = limit
        



    def load(self) -> list[PreferenceRow]:
        """ Load HH-RLHF data and return list of PreferenceRow Objects."""
        dataset = load_dataset("Anthropic/hh-rlhf", split=self.split)
        
        if self.limit:
            dataset = dataset.select(range(self.limit))
        

        rows = []
        for idx, example in enumerate(dataset):
            chosen_prompt, chosen_response = parse_conversation(example["chosen"])
            rejected_prompt, rejected_response = parse_conversation(example["rejected"])
            row = PreferenceRow(
                prompt = chosen_prompt,
                chosen = chosen_response,
                rejected = rejected_response,
                row_id=f"hh-rlhf-{self.split}-{idx}"
            )
            rows.append(row)

        
        return rows