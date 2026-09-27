"""tests/test_adapters.py -- adapter command and parser behaviour."""
from __future__ import annotations

from bhairava.core.executor import ExecContext, ExecResult
from bhairava.tools.adapters.httpx import HttpxAdapter
from bhairava.tools.adapters.nuclei import NucleiAdapter
from bhairava.tools.adapters.subfinder import SubfinderAdapter
from bhairava.tools.registry import default_registry


def _result(tool, stdout):
    return ExecResult(tool=tool, target="t", args=[], exit_code=0,
                     stdout=stdout, stderr="", duration_ms=1)


def test_subfinder_command():
    a = SubfinderAdapter()
    cmd = a.build_command(ExecContext(target="example.com"))
    assert cmd[0] == "subfinder"
    assert "-d" in cmd and "example.com" in cmd


def test_subfinder_parse():
    a = SubfinderAdapter()
    out = a.parse_output(_result("subfinder", "a.example.com\nB.EXAMPLE.COM\n\n"))
    hosts = [r["host"] for r in out]
    assert "a.example.com" in hosts
    assert "b.example.com" in hosts  # lowercased
    assert all(r["source"] == "subfinder" for r in out)


def test_httpx_parse():
    a = HttpxAdapter()
    out = a.parse_output(_result("httpx", "https://x.test [200]\n"))
    assert out[0]["url"] == "https://x.test"
    assert out[0]["status_code"] == 200


def test_nuclei_parse_jsonl():
    a = NucleiAdapter()
    line = '{"template-id":"cve-test","info":{"name":"Test","severity":"HIGH"},"host":"https://x.test","matched-at":"https://x.test/p"}'
    out = a.parse_output(_result("nuclei", line + "\nnot-json\n"))
    assert len(out) == 1
    assert out[0]["template_id"] == "cve-test"
    assert out[0]["severity"] == "high"
    assert out[0]["matched_at"] == "https://x.test/p"


def test_registry_has_three_default_adapters():
    r = default_registry()
    names = set(r.names())
    assert {"subfinder", "httpx", "nuclei"}.issubset(names)
