from __future__ import annotations

from pathlib import Path
import json


class PublicSourceLoader:
    """Loads prospect candidates collected from public sources.

    In production this class can be replaced with API connectors.
    """

    def __init__(self, data_file: Path):
        self.data_file = data_file

    def load_candidates(self) -> list[dict]:
        with self.data_file.open("r", encoding="utf-8") as f:
            return json.load(f)
