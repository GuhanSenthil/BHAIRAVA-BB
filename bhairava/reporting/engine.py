"""bhairava.reporting.engine -- orchestrate report generation."""
from __future__ import annotations
from pathlib import Path

from ..findings.models import Finding
from . import markdown as md
from . import json_report as js
from . import html as html_mod


FORMATS = ("markdown", "json", "html")


def write_report(
    findings: list[Finding],
    out_dir: str | Path,
    target: str = "",
    program: str = "",
    formats: tuple[str, ...] = ("markdown", "json", "html"),
) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    if "markdown" in formats:
        p = out / "report.md"
        p.write_text(md.render(findings, target=target, program=program),
                     encoding="utf-8")
        written["markdown"] = p

    if "json" in formats:
        p = out / "report.json"
        p.write_text(js.render(findings, target=target, program=program),
                     encoding="utf-8")
        written["json"] = p

    if "html" in formats:
        p = out / "report.html"
        p.write_text(html_mod.render(findings, target=target, program=program),
                     encoding="utf-8")
        written["html"] = p

    return written
