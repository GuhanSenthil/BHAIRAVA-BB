"""bhairava.findings.lifecycle -- state machine for findings."""
from __future__ import annotations
from .models import Finding


# Allowed transitions
_TRANSITIONS: dict[str, set[str]] = {
    "CANDIDATE": {"NEEDS_REVIEW", "REJECTED", "DUPLICATE"},
    "NEEDS_REVIEW": {"CONFIRMED", "REJECTED", "DUPLICATE"},
    "CONFIRMED": {"REPORTED", "DUPLICATE"},
    "REJECTED": set(),
    "DUPLICATE": set(),
    "REPORTED": set(),
}


class LifecycleError(ValueError):
    pass


def transition(finding: Finding, new_status: str) -> None:
    current = finding.status
    allowed = _TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise LifecycleError(
            f"illegal transition {current} -> {new_status} "
            f"(allowed: {sorted(allowed)})"
        )
    finding.status = new_status


def can_transition(finding: Finding, new_status: str) -> bool:
    return new_status in _TRANSITIONS.get(finding.status, set())


def promote_to_review(f: Finding) -> None:
    if f.status == "CANDIDATE":
        transition(f, "NEEDS_REVIEW")


def confirm(f: Finding) -> None:
    """Human or validation engine confirms a finding."""
    if f.status == "CANDIDATE":
        transition(f, "NEEDS_REVIEW")
    if f.status == "NEEDS_REVIEW":
        transition(f, "CONFIRMED")


def reject(f: Finding) -> None:
    if f.status in ("CANDIDATE", "NEEDS_REVIEW"):
        transition(f, "REJECTED")


def mark_duplicate(f: Finding) -> None:
    if f.status in ("CANDIDATE", "NEEDS_REVIEW", "CONFIRMED"):
        transition(f, "DUPLICATE")


def mark_reported(f: Finding) -> None:
    if f.status == "CONFIRMED":
        transition(f, "REPORTED")
