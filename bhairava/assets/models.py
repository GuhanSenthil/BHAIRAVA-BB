"""Asset Intelligence domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any


class AssetType(StrEnum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    URL = "url"
    ENDPOINT = "endpoint"
    IP = "ip"
    SERVICE = "service"


class ScopeStatus(StrEnum):
    UNKNOWN = "unknown"
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class Asset:
    """Normalized security-research asset."""

    asset_id: str
    asset_type: AssetType
    canonical_value: str
    source: str
    first_seen: str
    last_seen: str
    parent_asset_id: str | None = None
    http_status: int | None = None
    technologies: list[str] = field(default_factory=list)
    scope_status: ScopeStatus = ScopeStatus.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        asset_type: AssetType,
        canonical_value: str,
        source: str,
        *,
        parent_asset_id: str | None = None,
        http_status: int | None = None,
        technologies: list[str] | None = None,
        scope_status: ScopeStatus = ScopeStatus.UNKNOWN,
        metadata: dict[str, Any] | None = None,
    ) -> "Asset":
        """Create an asset with a deterministic stable ID."""
        normalized = canonical_value.strip().lower()
        digest = sha256(
            f"{asset_type.value}:{normalized}".encode("utf-8")
        ).hexdigest()[:24]

        timestamp = utc_now()

        return cls(
            asset_id=f"asset_{digest}",
            asset_type=asset_type,
            canonical_value=normalized,
            source=source,
            first_seen=timestamp,
            last_seen=timestamp,
            parent_asset_id=parent_asset_id,
            http_status=http_status,
            technologies=sorted(set(technologies or [])),
            scope_status=scope_status,
            metadata=metadata or {},
        )

    def touch(self, source: str | None = None) -> None:
        """Update last-seen metadata."""
        self.last_seen = utc_now()
        if source and source not in self.source.split(","):
            self.source = f"{self.source},{source}"

    def add_technology(self, technology: str) -> None:
        """Add a normalized technology name."""
        value = technology.strip()
        if value and value not in self.technologies:
            self.technologies.append(value)
            self.technologies.sort()
