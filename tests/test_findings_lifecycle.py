"""tests for finding state transitions."""
import pytest

from bhairava.findings.lifecycle import (
    LifecycleError,
    can_transition,
    confirm,
    mark_duplicate,
    mark_reported,
    promote_to_review,
    reject,
    transition,
)
from bhairava.findings.models import Finding


def test_candidate_to_needs_review():
    f = Finding(title="X")
    promote_to_review(f)
    assert f.status == "NEEDS_REVIEW"


def test_confirm_path():
    f = Finding(title="X")
    confirm(f)
    assert f.status == "CONFIRMED"


def test_confirm_from_review():
    f = Finding(title="X", status="NEEDS_REVIEW")
    confirm(f)
    assert f.status == "CONFIRMED"


def test_reject_from_candidate():
    f = Finding(title="X")
    reject(f)
    assert f.status == "REJECTED"


def test_reject_from_terminal_state_fails():
    f = Finding(title="X", status="REJECTED")
    with pytest.raises(LifecycleError):
        reject(f)


def test_duplicate_from_candidate():
    f = Finding(title="X")
    mark_duplicate(f)
    assert f.status == "DUPLICATE"


def test_reported_only_from_confirmed():
    f = Finding(title="X", status="CONFIRMED")
    mark_reported(f)
    assert f.status == "REPORTED"


def test_illegal_direct_transition():
    f = Finding(title="X")
    with pytest.raises(LifecycleError):
        transition(f, "CONFIRMED")


def test_can_transition_helper():
    f = Finding(title="X")
    assert can_transition(f, "NEEDS_REVIEW")
    assert not can_transition(f, "CONFIRMED")
