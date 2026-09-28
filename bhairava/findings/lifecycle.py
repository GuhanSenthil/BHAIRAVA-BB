"""Finding lifecycle supporting both legacy status and V6 state."""

from __future__ import annotations

from .models import Finding, FindingState


class LifecycleError(ValueError):
    """Raised when an invalid finding lifecycle transition is requested."""


_ALLOWED = {
    FindingState.CANDIDATE: {
        FindingState.NEEDS_REVIEW,
        FindingState.DUPLICATE,
        FindingState.REJECTED,
    },
    FindingState.NEEDS_REVIEW: {
        FindingState.CONFIRMED,
        FindingState.DUPLICATE,
        FindingState.REJECTED,
    },
    FindingState.CONFIRMED: {
        FindingState.REPORTED,
        FindingState.DUPLICATE,
        FindingState.REJECTED,
    },
    FindingState.REPORTED: set(),
    FindingState.DUPLICATE: set(),
    FindingState.REJECTED: set(),
}


def _state(finding: Finding) -> FindingState:
    value = getattr(finding, "state", None)

    if isinstance(value, FindingState):
        return value

    value = str(getattr(finding, "status", "CANDIDATE")).upper()

    return FindingState(value)


def can_transition(
    current,
    new_state,
) -> bool:
    """
    Compatibility helper.

    Accepts either:
        can_transition(FindingState.CANDIDATE, FindingState.NEEDS_REVIEW)
    or:
        can_transition(finding, "NEEDS_REVIEW")
    """
    from .models import Finding

    if isinstance(current, Finding):
        current_state = _state(current)
    elif isinstance(current, FindingState):
        current_state = current
    else:
        current_state = FindingState(str(current).upper())

    if isinstance(new_state, FindingState):
        target_state = new_state
    else:
        target_state = FindingState(str(new_state).upper())

    return target_state in _ALLOWED.get(current_state, set())


def transition(
    finding: Finding,
    new_state: FindingState | str,
) -> Finding:
    current = _state(finding)

    target = (
        new_state
        if isinstance(new_state, FindingState)
        else FindingState(str(new_state).upper())
    )

    if not can_transition(current, target):
        raise LifecycleError(
            f"Invalid finding transition: "
            f"{current.value} -> {target.value}"
        )

    finding.set_state(target)

    return finding


def promote_to_review(finding: Finding) -> Finding:
    return transition(finding, FindingState.NEEDS_REVIEW)


def confirm(finding: Finding) -> Finding:
    current = _state(finding)

    # Preserve legacy behavior: candidate → review → confirmed.
    if current == FindingState.CANDIDATE:
        transition(finding, FindingState.NEEDS_REVIEW)

    return transition(finding, FindingState.CONFIRMED)


def reject(finding: Finding) -> Finding:
    current = _state(finding)

    if current in (
        FindingState.CANDIDATE,
        FindingState.NEEDS_REVIEW,
        FindingState.CONFIRMED,
    ):
        return transition(finding, FindingState.REJECTED)

    raise LifecycleError(
        f"Cannot reject finding in state {current.value}"
    )


def mark_duplicate(finding: Finding) -> Finding:
    current = _state(finding)

    if current in (
        FindingState.CANDIDATE,
        FindingState.NEEDS_REVIEW,
        FindingState.CONFIRMED,
    ):
        return transition(finding, FindingState.DUPLICATE)

    raise LifecycleError(
        f"Cannot mark duplicate from state {current.value}"
    )


def mark_reported(finding: Finding) -> Finding:
    current = _state(finding)

    if current != FindingState.CONFIRMED:
        raise LifecycleError(
            f"Cannot mark reported from state {current.value}"
        )

    return transition(finding, FindingState.REPORTED)
