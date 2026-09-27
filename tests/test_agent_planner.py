"""tests for planner integration with policy + scope."""
from __future__ import annotations
from unittest import mock

import pytest

from bhairava.agent.planner import Planner
from bhairava.scope_guard import Scope, ScopeGuard


@pytest.fixture
def guard():
    return ScopeGuard(Scope(name="T", domains=["example.com", "*.example.com"]))


def _make_planner(guard, response_text):
    ai_cfg = {"enabled": True, "provider": "ollama", "model": "test"}
    p = Planner(ai_cfg, guard)
    # Bypass provider construction and stub chat()
    class FakeProvider:
        def available(self): return True
        def chat(self, system, user): return response_text
    p.provider = FakeProvider()
    return p


def test_planner_accepts_valid_plan(guard):
    payload = '{"steps":[{"module":"discover","tool":"httpx","target":"app.example.com","reason":"r"}]}'
    p = _make_planner(guard, payload)
    result = p.plan()
    assert len(result.steps) == 1
    assert result.steps[0]["tool"] == "httpx"


def test_planner_rejects_out_of_scope_target(guard):
    payload = '{"steps":[{"module":"discover","tool":"httpx","target":"evil.com","reason":"r"}]}'
    p = _make_planner(guard, payload)
    result = p.plan()
    assert len(result.steps) == 0
    assert any("out of scope" in r for r in result.rejected)


def test_planner_rejects_forbidden_tool(guard):
    payload = '{"steps":[{"module":"scan","tool":"metasploit","target":"app.example.com","reason":"r"}]}'
    p = _make_planner(guard, payload)
    result = p.plan()
    assert len(result.steps) == 0


def test_planner_handles_bad_json(guard):
    p = _make_planner(guard, "the model refused")
    result = p.plan()
    assert result.error is not None
    assert result.steps == []


def test_planner_handles_markdown_wrapped_json(guard):
    payload = '```json\n{"steps":[]}\n```'
    p = _make_planner(guard, payload)
    result = p.plan()
    assert result.error is None
    assert result.steps == []


def test_planner_disabled_by_default(guard):
    p = Planner({"enabled": False}, guard)
    result = p.plan()
    assert result.error == "AI disabled in config"
