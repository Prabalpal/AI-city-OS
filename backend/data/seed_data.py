import json
from pathlib import Path


def load_seed_data() -> dict:
    file_path = Path(__file__).resolve().parent / "seed_data.json"
    with file_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)
