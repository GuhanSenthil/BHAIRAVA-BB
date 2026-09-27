"""tests for analyzer schema validation."""
from __future__ import annotations

import pytest

from bhairava.agent.analyzer import Analyzer
from bhairava.findings.models import Finding


def _make_analyzer(response_text):
    a = Analyzer({"enabled": True, "provider": "ollama", "model": "test"})
    class FakeProvider:
        def available(self): return True
        def chat(self, system, user): return response_text
    a.provider = FakeProvider()
    return a


def test_analyzer_parses_valid_response():
    payload = ('{"severity_assessment":"high","confidence_adjust":0.7,'
               '"summary":"XSS confirmed","verification_steps":["a","b"],'
               '"notes":"ok"}')
    a = _make_analyzer(payload)
    r = a.analyze(Finding(title="XSS", url="https://x.test/p"))
    assert r.analysis is not None
    assert r.analysis["severity_assessment"] == "high"
    assert r.analysis["confidence_adjust"] == 0.7


def test_analyzer_handles_bad_json():
    a = _make_analyzer("no JSON here")
    r = a.analyze(Finding(title="XSS", url="https://x.test/p"))
    assert r.analysis is None
    assert r.error is not None


def test_analyzer_disabled():
    a = Analyzer({"enabled": False})
    r = a.analyze(Finding(title="X", url="https://x.test/"))
    assert r.error == "AI disabled"


def test_analyzer_strips_markdown_fences():
    payload = '```json\n{"severity_assessment":"low","summary":"x"}\n```'
    a = _make_analyzer(payload)
    r = a.analyze(Finding(title="X", url="https://x.test/"))
    assert r.analysis is not None
    assert r.analysis["severity_assessment"] == "low"
