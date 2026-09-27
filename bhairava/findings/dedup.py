"""bhairava.findings.dedup -- merge duplicate findings."""
from __future__ import annotations

from .models import Finding

_SEVERITY_RANK = {
    "info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4,
}


def dedupe(findings: list[Finding]) -> list[Finding]:
    """Merge findings with identical fingerprints.

    Merged result keeps:
      - the highest severity seen
      - the highest confidence seen
      - the union of evidence, references, source_tools
    """
    by_fp: dict[str, Finding] = {}
    for f in findings:
        fp = f.fingerprint()
        existing = by_fp.get(fp)
        if existing is None:
            by_fp[fp] = f
            continue
        # merge into existing
        if _SEVERITY_RANK.get(f.severity, 0) > _SEVERITY_RANK.get(existing.severity, 0):
            existing.severity = f.severity
        existing.confidence = max(existing.confidence, f.confidence)
        for e in f.evidence:
            if e not in existing.evidence:
                existing.evidence.append(e)
        for r in f.references:
            if r not in existing.references:
                existing.references.append(r)
        for t in f.source_tools:
            if t not in existing.source_tools:
                existing.source_tools.append(t)
        if not existing.description and f.description:
            existing.description = f.description
        if not existing.remediation and f.remediation:
            existing.remediation = f.remediation
    return list(by_fp.values())
