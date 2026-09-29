"""Canonical Finding models with legacy + V6 compatibility."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlparse, urlunparse

SEVERITIES = ("info", "low", "medium", "high", "critical")

STATUSES = (
    "CANDIDATE",
    "NEEDS_REVIEW",
    "CONFIRMED",
    "DUPLICATE",
    "REJECTED",
    "REPORTED",
)


class FindingState(str, Enum):
    CANDIDATE = "CANDIDATE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    REPORTED = "REPORTED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id() -> str:
    return "finding-" + uuid.uuid4().hex[:10]


@dataclass
class Observation:
    """A V6 deterministic security observation."""

    source: str
    target: str
    endpoint: str = ""
    parameter: str = ""
    category: str = ""
    title: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        """
        Stable correlation fingerprint.

        Query-string values are excluded. The fingerprint is based on
        target host, endpoint path, parameter, and category.
        """
        candidate = self.endpoint or self.target
        host = self.target.strip().lower()
        path = ""

        try:
            parsed = urlparse(candidate)
            if parsed.hostname:
                host = parsed.hostname.lower()
            path = parsed.path or ""
        except Exception:
            path = candidate

        raw = "|".join(
            [
                host,
                path.strip().lower(),
                self.parameter.strip().lower(),
                self.category.strip().lower(),
            ]
        )

        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["fingerprint"] = self.fingerprint()
        return data


@dataclass
class Finding:
    """
    Canonical finding model.

    The model intentionally supports both the original BHAIRAVA
    finding API and the V6 correlation/evidence API.
    """

    # Legacy fields
    title: str = ""
    severity: str = "info"
    confidence: float = 0.0
    host: str = ""
    url: str = ""
    parameter: str = ""
    category: str = ""
    description: str = ""
    impact: str = ""
    remediation: str = ""
    evidence: list[Any] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    source_tools: list[str] = field(default_factory=list)
    status: str = "CANDIDATE"
    id: str = field(default_factory=_short_id)
    timestamp: str = field(default_factory=_now)
    job_id: str = ""
    template_id: str = ""
    matched_at: str = ""

    # V6 fields
    finding_id: str = ""
    target: str = ""
    endpoint: str = ""
    observations: list[Observation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    state: FindingState = FindingState.CANDIDATE

    def __post_init__(self) -> None:
        # Normalize severity.
        severity = str(self.severity).lower()
        if severity not in SEVERITIES:
            severity = "info"
        self.severity = severity

        # Normalize legacy status.
        explicit_status = str(self.status).upper()
        if explicit_status not in STATUSES:
            explicit_status = "CANDIDATE"

        # If V6 state was explicitly supplied, use it.
        if isinstance(self.state, FindingState):
            state_value = self.state.value
        else:
            try:
                state_value = FindingState(str(self.state).upper()).value
            except (ValueError, TypeError):
                state_value = "CANDIDATE"

        # A non-default legacy status should take precedence over the
        # dataclass default V6 state.
        if explicit_status != "CANDIDATE" and state_value == "CANDIDATE":
            state_value = explicit_status

        self.status = state_value
        self.state = FindingState(state_value)

        # V6 identity compatibility.
        if not self.finding_id:
            self.finding_id = self.id

        if not self.id:
            self.id = self.finding_id or _short_id()

        # Keep both target and host useful.
        if not self.host and self.target:
            try:
                parsed = urlparse(self.target)
                self.host = parsed.hostname or self.target
            except Exception:
                self.host = self.target

        if not self.target:
            self.target = self.host

        # Keep endpoint and URL interoperable.
        if not self.endpoint:
            self.endpoint = self.url

        if not self.url:
            self.url = self.endpoint

        # Derive host from URL when possible.
        if not self.host and self.url:
            try:
                self.host = urlparse(self.url).hostname or ""
            except Exception:
                self.host = ""

        # Legacy callers sometimes provide evidence as a dictionary.
        if self.evidence is None:
            self.evidence = []
        elif isinstance(self.evidence, dict):
            self.evidence = [self.evidence]

    def set_state(self, state: FindingState | str) -> None:
        """Synchronize the V6 state and legacy status fields."""
        if isinstance(state, FindingState):
            normalized = state
        else:
            normalized = FindingState(str(state).upper())

        self.state = normalized
        self.status = normalized.value

    def add_observation(self, observation: Observation) -> None:
        self.observations.append(observation)

        if observation.source and observation.source not in self.source_tools:
            self.source_tools.append(observation.source)

        if not self.target:
            self.target = observation.target

        if not self.endpoint:
            self.endpoint = observation.endpoint

        if not self.parameter:
            self.parameter = observation.parameter

        if not self.category:
            self.category = observation.category

        if not self.title:
            self.title = observation.title

    def fingerprint(self) -> str:
        """
        Stable finding fingerprint.

        Query-string values are intentionally excluded.
        """
        candidate = self.url or self.endpoint

        host = self.host or self.target
        path = ""

        try:
            parsed = urlparse(candidate)

            if parsed.hostname:
                host = parsed.hostname

            path = parsed.path or ""

            # Rebuild without query/fragment to make the intent explicit.
            _ = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    "",
                    "",
                )
            )
        except Exception:
            path = candidate

        raw = "|".join(
            [
                (host or "").strip().lower(),
                path.strip().lower(),
                self.parameter.strip().lower(),
                self.category.strip().lower(),
                self.template_id.strip().lower(),
            ]
        )

        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        """Serialize both legacy and V6 fields."""
        data = asdict(self)

        state = data.get("state")
        if isinstance(state, FindingState):
            data["state"] = state.value

        # Keep legacy status synchronized.
        data["status"] = self.status

        # Dataclasses normally serialize nested enums as enum instances;
        # normalize observations if needed.
        serialized_observations = []
        for observation in self.observations:
            if isinstance(observation, Observation):
                serialized_observations.append(observation.to_dict())
            else:
                serialized_observations.append(observation)

        data["observations"] = serialized_observations
        data["fingerprint"] = self.fingerprint()

        return data
