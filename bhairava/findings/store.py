"""bhairava.findings.store -- simple in-memory + JSON persistence."""
from __future__ import annotations

import json
from pathlib import Path

from .models import Finding


class FindingStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._findings: dict[str, Finding] = {}

    def add(self, finding: Finding) -> None:
        self._findings[finding.id] = finding

    def add_many(self, findings: list[Finding]) -> None:
        for f in findings:
            self.add(f)

    def all(self) -> list[Finding]:
        return list(self._findings.values())

    def by_status(self, status: str) -> list[Finding]:
        return [f for f in self._findings.values() if f.status == status]

    def save(self) -> Path | None:
        if not self.path:
            return None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [f.to_dict() for f in self._findings.values()]
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.path

    def load(self) -> None:
        if not self.path or not self.path.exists():
            return
        rows = json.loads(self.path.read_text(encoding="utf-8"))
        for row in rows:
            row.pop("fingerprint", None)
            self.add(Finding(**row))
