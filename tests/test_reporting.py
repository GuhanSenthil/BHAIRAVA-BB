"""tests for report generation."""
import json

from bhairava.findings.models import Finding
from bhairava.reporting import html as html_mod
from bhairava.reporting import json_report as js
from bhairava.reporting import markdown as md
from bhairava.reporting.engine import write_report


def _findings():
    return [
        Finding(title="XSS", severity="high", status="CONFIRMED",
                url="https://app.example.com/s", parameter="q",
                source_tools=["nuclei"]),
        Finding(title="Header missing", severity="low", status="CANDIDATE",
                url="https://app.example.com/", category="header"),
    ]


def test_markdown_renders_findings():
    out = md.render(_findings(), target="app.example.com")
    assert "# BHAIRAVA-BB Report" in out
    assert "XSS" in out
    assert "Header missing" in out
    assert "CONFIRMED" in out


def test_json_renders_valid():
    out = js.render(_findings(), target="app.example.com")
    data = json.loads(out)
    assert data["count"] == 2
    assert data["target"] == "app.example.com"
    assert len(data["findings"]) == 2


def test_html_renders_findings():
    out = html_mod.render(_findings(), target="app.example.com")
    assert "<!doctype html>" in out.lower()
    assert "XSS" in out
    assert "app.example.com" in out


def test_write_report_creates_files(tmp_path):
    paths = write_report(_findings(), tmp_path, target="x", program="P")
    assert "markdown" in paths
    assert "json" in paths
    assert "html" in paths
    for p in paths.values():
        assert p.exists()
        assert p.stat().st_size > 0
