"""tests for the detection engine."""
from __future__ import annotations
from unittest import mock

import pytest

from bhairava.core.executor import ExecResult, ToolExecutor
from bhairava.detection.engine import DetectionEngine
from bhairava.scope_guard import Scope, ScopeGuard
from bhairava.tools.base import ToolAdapter
from bhairava.tools.registry import ToolRegistry


class FakeNuclei(ToolAdapter):
    name = "nuclei"
    binary = "nuclei"
    def __init__(self, rows=None):
        self._rows = rows or []
    def available(self):
        return True
    def build_command(self, ctx):
        return ["nuclei", "-u", ctx.target]
    def parse_output(self, result):
        return self._rows


@pytest.fixture
def guard():
    return ScopeGuard(Scope(name="T", domains=["example.com", "*.example.com"]))


def test_scan_blocks_out_of_scope(guard):
    ex = ToolExecutor(guard)
    reg = ToolRegistry()
    reg.register(FakeNuclei())
    engine = DetectionEngine(ex, reg, guard)
    r = engine.run("evil.com")
    assert r.findings == []
    assert any("scope violation" in e.lower() for e in r.errors)


def test_scan_produces_findings(guard):
    rows = [
        {"template_id": "xss-reflected", "name": "Reflected XSS",
         "severity": "high", "host": "app.example.com",
         "matched_at": "https://app.example.com/search?q=1",
         "type": "http"},
    ]
    ex = ToolExecutor(guard)
    reg = ToolRegistry()
    reg.register(FakeNuclei(rows))
    engine = DetectionEngine(ex, reg, guard)

    fake = ExecResult(tool="nuclei", target="app.example.com", args=[],
                      exit_code=0, stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake):
        r = engine.run("app.example.com")

    assert len(r.findings) == 1
    f = r.findings[0]
    assert f.severity == "high"
    assert f.status == "CANDIDATE"
    assert f.source_tools == ["nuclei"]
    assert f.template_id == "xss-reflected"


def test_scan_drops_out_of_scope_matches(guard):
    rows = [
        {"template_id": "x", "name": "X", "severity": "high",
         "matched_at": "https://evil.com/p"},
    ]
    ex = ToolExecutor(guard)
    reg = ToolRegistry()
    reg.register(FakeNuclei(rows))
    engine = DetectionEngine(ex, reg, guard)
    fake = ExecResult(tool="nuclei", target="app.example.com", args=[],
                      exit_code=0, stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake):
        r = engine.run("app.example.com")
    assert r.findings == []
    assert r.raw_count == 1
