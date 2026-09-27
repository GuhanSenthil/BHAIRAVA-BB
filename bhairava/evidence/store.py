"""bhairava.evidence.store -- in-memory + JSON evidence store."""
from __future__ import annotations

import json
from pathlib import Path


class EvidenceStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._records: dict[str, list[dict]] = {}

    def add(self, finding_id: str, record: dict) -> None:
        self._records.setdefault(finding_id, []).append(record)

    def get(self, finding_id: str) -> list[dict]:
        return list(self._records.get(finding_id, []))

    def all(self) -> dict[str, list[dict]]:
        return dict(self._records)

    def save(self) -> Path | None:
        if not self.path:
            return None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return self.path
