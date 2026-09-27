"""bhairava.reporting.markdown -- markdown report renderer."""
from __future__ import annotations
from datetime import datetime, timezone
from ..findings.models import Finding


_SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def render(findings: list[Finding], target: str = "", program: str = "") -> str:
    lines = []
    lines.append("# BHAIRAVA-BB Report\n")
    if program:
        lines.append(f"**Program:** {program}\n")
    if target:
        lines.append(f"**Target:** {target}\n")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
    lines.append(f"**Findings:** {len(findings)}\n")

    by_sev: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        by_status[f.status] = by_status.get(f.status, 0) + 1

    lines.append("\n## Summary\n")
    lines.append("| Severity | Count |")
    lines.append("|---|---|")
    for sev in ("critical", "high", "medium", "low", "info"):
        if sev in by_sev:
            lines.append(f"| {sev.capitalize()} | {by_sev[sev]} |")

    lines.append("\n| Status | Count |")
    lines.append("|---|---|")
    for st, n in sorted(by_status.items()):
        lines.append(f"| {st} | {n} |")

    sorted_f = sorted(findings, key=lambda x: _SEV_ORDER.get(x.severity, 99))

    for f in sorted_f:
        lines.append("\n---\n")
        lines.append(f"## {f.title}\n")
        lines.append(f"- **ID:** `{f.id}`")
        lines.append(f"- **Severity:** {f.severity}")
        lines.append(f"- **Confidence:** {f.confidence:.2f}")
        lines.append(f"- **Status:** {f.status}")
        if f.host:
            lines.append(f"- **Host:** {f.host}")
        if f.url:
            lines.append(f"- **URL:** {f.url}")
        if f.parameter:
            lines.append(f"- **Parameter:** {f.parameter}")
        if f.template_id:
            lines.append(f"- **Template:** `{f.template_id}`")
        if f.source_tools:
            lines.append(f"- **Source tools:** {', '.join(f.source_tools)}")

        if f.description:
            lines.append(f"\n### Description\n\n{f.description}")
        if f.impact:
            lines.append(f"\n### Impact\n\n{f.impact}")

        if f.evidence:
            lines.append("\n### Evidence\n")
            for i, ev in enumerate(f.evidence, 1):
                lines.append(f"**Evidence {i}** (`{ev.get('kind', 'unknown')}`)")
                if ev.get("hash"):
                    lines.append(f"- Hash: `{ev['hash']}`")
                if ev.get("tool"):
                    lines.append(f"- Tool: `{ev['tool']}`")
                if ev.get("note"):
                    lines.append(f"- Note: {ev['note']}")

        if f.remediation:
            lines.append(f"\n### Remediation\n\n{f.remediation}")
        if f.references:
            lines.append("\n### References\n")
            for r in f.references:
                lines.append(f"- {r}")

    return "\n".join(lines) + "\n"
