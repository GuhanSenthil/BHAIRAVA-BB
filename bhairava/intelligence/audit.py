"""V7 deterministic intelligence audit trail."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AuditLog:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._events: list[AuditEvent] = []

    def record(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=dict(details or {}),
        )
        self._events.append(event)
        return event

    def all(self) -> list[AuditEvent]:
        return list(self._events)

    def save(self) -> Path | None:
        if self.path is None:
            return None

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(event) for event in self._events]
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return self.path
