"""tests for the recon engine."""
from __future__ import annotations

from unittest import mock

import pytest

from bhairava.core.executor import ExecResult, ToolExecutor
from bhairava.recon.engine import ReconEngine
from bhairava.scope_guard import Scope, ScopeGuard
from bhairava.tools.base import ToolAdapter
from bhairava.tools.registry import ToolRegistry


class FakeAdapter(ToolAdapter):
    name = "fake"
    binary = "fake"
    def __init__(self, name, hosts=None):
        self.name = name
        self._hosts = hosts or []
    def available(self):
        return True
    def build_command(self, ctx):
        return ["fake", ctx.target]
    def parse_output(self, result):
        return [{"host": h, "source": self.name} for h in self._hosts]


@pytest.fixture
def guard():
    return ScopeGuard(Scope(name="T", domains=["example.com", "*.example.com"]))


def test_recon_blocks_out_of_scope(guard):
    ex = ToolExecutor(guard)
    engine = ReconEngine(ex, ToolRegistry(), guard)
    r = engine.run("evil.com")
    assert r.hosts == []
    assert any("scope violation" in e.lower() for e in r.errors)


def test_recon_merges_and_dedupes(guard):
    reg = ToolRegistry()
    reg.register(FakeAdapter("subfinder", ["a.example.com", "b.example.com"]))
    reg.register(FakeAdapter("amass", ["b.example.com", "c.example.com"]))
    ex = ToolExecutor(guard)

    fake_result = ExecResult(tool="x", target="example.com", args=[], exit_code=0,
                             stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake_result):
        engine = ReconEngine(ex, reg, guard)
        # crt.sh makes a network call -- stub it
        with mock.patch("bhairava.recon.engine.crtsh.query", return_value=[]):
            r = engine.run("example.com")
    assert sorted(r.hosts) == ["a.example.com", "b.example.com", "c.example.com"]
    # sources counts UNIQUE new contributions per source
    # subfinder: a, b (2 new)
    # amass:     c only (b was already seen) -> 1 new
    assert r.sources.get("subfinder") == 2
    assert r.sources.get("amass") == 1


def test_recon_filters_out_of_scope_discovered_hosts(guard):
    reg = ToolRegistry()
    reg.register(FakeAdapter("subfinder", ["ok.example.com", "evil.com"]))
    ex = ToolExecutor(guard)
    fake_result = ExecResult(tool="x", target="example.com", args=[], exit_code=0,
                             stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake_result):
        engine = ReconEngine(ex, reg, guard)
        with mock.patch("bhairava.recon.engine.crtsh.query", return_value=[]):
            r = engine.run("example.com")
    assert "ok.example.com" in r.hosts
    assert "evil.com" not in r.hosts
