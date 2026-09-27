"""bhairava.findings.models -- canonical Finding model."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib
import uuid


SEVERITIES = ("info", "low", "medium", "high", "critical")

STATUSES = (
    "CANDIDATE",
    "NEEDS_REVIEW",
    "CONFIRMED",
    "DUPLICATE",
    "REJECTED",
    "REPORTED",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id() -> str:
    return "finding-" + uuid.uuid4().hex[:10]


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
    impact: str = ""
    remediation: str = ""
    evidence: list[dict] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    source_tools: list[str] = field(default_factory=list)
    status: str = "CANDIDATE"
    id: str = field(default_factory=_short_id)
    timestamp: str = field(default_factory=_now)
    job_id: str = ""
    template_id: str = ""
    matched_at: str = ""

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            self.severity = "info"
        if self.status not in STATUSES:
            self.status = "CANDIDATE"
        if not self.host and self.url:
            from urllib.parse import urlparse
            self.host = urlparse(self.url).hostname or ""

    def fingerprint(self) -> str:
        """Stable key for correlation and dedup."""
        from urllib.parse import urlparse
        p = urlparse(self.url or self.matched_at or "")
        path = p.path.rstrip("/") or "/"
        key = "|".join([
            (p.hostname or self.host or "").lower(),
            path.lower(),
            (self.parameter or "").lower(),
            (self.category or "").lower(),
            (self.template_id or "").lower(),
        ])
        return hashlib.sha1(key.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["fingerprint"] = self.fingerprint()
        return d
