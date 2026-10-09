"""V7 deterministic intelligence audit trail."""

from __future__ import annotations

import json
import re
import tempfile
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|"
    r"cookie|credential|private[_-]?key)",
    re.IGNORECASE,
)
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+\S+")


def _redact(value: Any, key: str = "") -> Any:
    """Return JSON-compatible audit details with sensitive values redacted."""
    if _SECRET_KEY_PATTERN.search(key):
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            str(item_key): _redact(item_value, str(item_key))
            for item_key, item_value in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]

    if isinstance(value, str):
        return _BEARER_PATTERN.sub("Bearer [REDACTED]", value)

    if value is None or isinstance(value, (bool, int, float)):
        return value

    return str(value)


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
        self._lock = threading.RLock()

        if self.path is not None and self.path.is_file():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(payload, list):
                    raise ValueError("Audit log must contain a JSON list")

                self._events = [
                    AuditEvent(
                        action=str(item["action"]),
                        entity_type=str(item["entity_type"]),
                        entity_id=str(item["entity_id"]),
                        details=_redact(item.get("details", {})),
                        timestamp=str(item["timestamp"]),
                    )
                    for item in payload
                    if isinstance(item, dict)
                ]
            except (
                OSError,
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    f"Unable to load audit log {self.path}: {exc}"
                ) from exc

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
            details=_redact(details or {}),
        )
        with self._lock:
            self._events.append(event)
        return event

    def all(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)

    def save(self) -> Path | None:
        if self.path is None:
            return None

        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = [asdict(event) for event in self._events]
            temporary_path: Path | None = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self.path.parent,
                    prefix=f".{self.path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    json.dump(payload, temporary_file, indent=2, ensure_ascii=False)
                    temporary_file.write("\n")

                temporary_path.replace(self.path)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

        return self.path
