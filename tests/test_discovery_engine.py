"""tests for the discovery engine."""
from __future__ import annotations

from unittest import mock

import pytest

from bhairava.core.executor import ExecResult, ToolExecutor
from bhairava.discovery.engine import DiscoveryEngine
from bhairava.scope_guard import Scope, ScopeGuard
from bhairava.tools.base import ToolAdapter
from bhairava.tools.registry import ToolRegistry


class FakeUrlAdapter(ToolAdapter):
    name = "fake"
    binary = "fake"
    def __init__(self, name, urls):
        self.name = name
        self._urls = urls
    def available(self):
        return True
    def build_command(self, ctx):
        return ["fake", ctx.target]
    def parse_output(self, result):
        return [{"url": u, "source": self.name} for u in self._urls]


@pytest.fixture
def guard():
    return ScopeGuard(Scope(name="T", domains=["example.com", "*.example.com"]))


def test_discovery_blocks_out_of_scope(guard):
    ex = ToolExecutor(guard)
    engine = DiscoveryEngine(ex, ToolRegistry(), guard)
    r = engine.run("evil.com")
    assert r.endpoints == []
    assert any("scope violation" in e.lower() for e in r.errors)


def test_discovery_filters_by_scope(guard):
    reg = ToolRegistry()
    reg.register(FakeUrlAdapter("httpx", [
        "https://app.example.com/a",
        "https://evil.com/b",
        "https://api.example.com/c",
    ]))
    ex = ToolExecutor(guard)
    fake = ExecResult(tool="x", target="example.com", args=[], exit_code=0,
                      stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake):
        engine = DiscoveryEngine(ex, reg, guard)
        r = engine.run("example.com")
    urls = [e["url"] for e in r.endpoints]
    assert "https://app.example.com/a" in urls
    assert "https://api.example.com/c" in urls
    assert "https://evil.com/b" not in urls


def test_discovery_parses_host_path_query(guard):
    reg = ToolRegistry()
    reg.register(FakeUrlAdapter("httpx", ["https://app.example.com/api?x=1"]))
    ex = ToolExecutor(guard)
    fake = ExecResult(tool="x", target="example.com", args=[], exit_code=0,
                      stdout="", stderr="", duration_ms=1)
    with mock.patch.object(ToolExecutor, "run", return_value=fake):
        engine = DiscoveryEngine(ex, reg, guard)
        r = engine.run("example.com")
    e = r.endpoints[0]
    assert e["host"] == "app.example.com"
    assert e["path"] == "/api"
    assert e["query"] == "x=1"
