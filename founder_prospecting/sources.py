from __future__ import annotations

from pathlib import Path
import json


class PublicSourceLoader:
    """Loads prospect candidates from seed and optional enrichment files.

    By default this reads the seed sample file used for local testing.
    For production-like runs, pass one or more ``extra_files`` containing
    normalized candidate payloads.
    """

    def __init__(self, data_file: Path, extra_files: list[Path] | None = None):
        self.data_file = data_file
        self.extra_files = extra_files or []

    def load_candidates(self) -> list[dict]:
        combined: list[dict] = []
        for path in [self.data_file, *self.extra_files]:
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as f:
                rows = json.load(f)
                if isinstance(rows, list):
                    combined.extend(rows)
        return combined

    def active_sources(self) -> list[str]:
        names: list[str] = []
        for path in [self.data_file, *self.extra_files]:
            if path.exists():
                names.append(path.name)
        return names
