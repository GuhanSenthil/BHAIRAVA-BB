"""Negative tests: out-of-scope targets must be blocked."""
import pytest
from bhairava.exceptions import ScopeViolation
from bhairava.scope_guard import Scope, ScopeGuard


@pytest.fixture
def guard():
    return ScopeGuard(Scope(
        name="Test",
        domains=["*.example.com", "api.test.io"],
        urls=["https://example.com"],
        excluded=["admin.example.com", "*.internal.example.com"],
    ))


def test_in_scope_wildcard(guard):
    assert guard.is_in_scope("https://app.example.com/x")
    assert guard.is_in_scope("sub.deep.example.com")


def test_out_of_scope(guard):
    assert not guard.is_in_scope("https://evil.com")
    assert not guard.is_in_scope("https://example.org")


def test_exclusion(guard):
    assert not guard.is_in_scope("https://admin.example.com")
    assert not guard.is_in_scope("https://db.internal.example.com")
    assert guard.is_in_scope("https://public.example.com")


def test_exact_url(guard):
    assert guard.is_in_scope("https://example.com")
    assert not guard.is_in_scope("https://example.com.evil.org")


def test_validate_raises_on_out_of_scope(guard):
    with pytest.raises(ScopeViolation):
        guard.validate_target("https://evil.com")


def test_validate_url_rejects_scheme(guard):
    with pytest.raises(ScopeViolation):
        guard.validate_url("ftp://app.example.com")


def test_decisions_are_recorded(guard):
    guard.validate_target("https://app.example.com")
    try:
        guard.validate_target("https://evil.com")
    except ScopeViolation:
        pass
    decisions = guard.summary()["decisions"]
    assert ("https://app.example.com", "ALLOWED") in decisions
    assert any(d[1] == "BLOCKED" for d in decisions)


def test_validate_many_filters(guard):
    ok = guard.validate_many([
        "https://app.example.com",
        "https://evil.com",
        "https://api.test.io",
    ])
    assert ok == ["https://app.example.com", "https://api.test.io"]
