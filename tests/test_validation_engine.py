"""tests for validation engine."""
from __future__ import annotations
from unittest import mock

import pytest

from bhairava.core.executor import ExecResult, ToolExecutor
from bhairava.findings.models import Finding
from bhairava.scope_guard import Scope, ScopeGuard
from bhairava.tools.base import ToolAdapter
from bhairava.tools.registry import ToolRegistry
from bhairava.validation.engine import ValidationEngine


class FakeDalfox(ToolAdapter):
    name = "dalfox"
    binary = "dalfox"
    def __init__(self, hits=None):
        self._hits = hits or []
    def available(self):
        return True
    def build_command(self, ctx):
        return ["dalfox", "url", ctx.target]
    def parse_output(self, result):
        return self._hits


@pytest.fixture
def guard():
    return ScopeGuard(Scope(name="T", domains=["example.com", "*.example.com"]))


def test_validation_confirms_on_hits(guard):
    reg = ToolRegistry()
    reg.register(FakeDalfox(hits=[{"url": "https://app.example.com/s", "param": "q"}]))
    ex = ToolExecutor(guard)
    engine = ValidationEngine(ex, reg, guard, auto_approve=True)
    f = Finding(title="XSS", url="https://app.example.com/s?q=1",
                parameter="q", category="xss", severity="high")

    fake = ExecResult(tool="dalfox", target="x", args=[], exit_code=0,
                      stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake):
        r = engine.validate(f)

    assert r.validated is True
    assert f.status == "CONFIRMED"


def test_validation_rejects_on_no_hits(guard):
    reg = ToolRegistry()
    reg.register(FakeDalfox(hits=[]))
    ex = ToolExecutor(guard)
    engine = ValidationEngine(ex, reg, guard, auto_approve=True)
    f = Finding(title="XSS", url="https://app.example.com/s?q=1",
                parameter="q", category="xss", severity="high")

    fake = ExecResult(tool="dalfox", target="x", args=[], exit_code=0,
                      stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake):
        r = engine.validate(f)

    assert r.rejected is True
    assert f.status == "REJECTED"


def test_validation_blocks_out_of_scope(guard):
    reg = ToolRegistry()
    reg.register(FakeDalfox(hits=[{"url": "x"}]))
    ex = ToolExecutor(guard)
    engine = ValidationEngine(ex, reg, guard, auto_approve=True)
    f = Finding(title="XSS", url="https://evil.com/p", category="xss")
    r = engine.validate(f)
    assert "scope violation" in (r.error or "").lower()
    assert f.status == "REJECTED"


def test_no_validator_for_category(guard):
    reg = ToolRegistry()
    ex = ToolExecutor(guard)
    engine = ValidationEngine(ex, reg, guard, auto_approve=True)
    f = Finding(title="SSRF", url="https://app.example.com/p", category="ssrf")
    r = engine.validate(f)
    assert "no validator" in (r.error or "").lower()
