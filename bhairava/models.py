"""bhairava.models -- Shared dataclasses."""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

STATUSES = ("CANDIDATE", "NEEDS_REVIEW", "CONFIRMED", "DUPLICATE", "REJECTED", "REPORTED")


@dataclass
class Finding:
    title: str
    severity: str = "info"
    confidence: float = 0.3
    host: str = ""
    url: str = ""
    parameter: str = ""
    category: str = "unknown"
    description: str = ""
    evidence: list[dict] = field(default_factory=list)
    remediation: str = ""
    references: list[str] = field(default_factory=list)
    source_tools: list[str] = field(default_factory=list)
    status: str = "CANDIDATE"
    id: str = field(default_factory=lambda: "finding-" + uuid.uuid4().hex[:10])
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Target:
    url: str
    host: str = ""
    status_code: int = 0
    title: str = ""
    content_type: str = ""
    server: str = ""
    technologies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
