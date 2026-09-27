"""bhairava.findings.correlation -- cross-tool finding correlation."""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Finding


@dataclass
class CorrelationGroup:
    fingerprint: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def tools(self) -> list[str]:
        s: set[str] = set()
        for f in self.findings:
            s.update(f.source_tools)
        return sorted(s)


def correlate(findings: list[Finding]) -> list[CorrelationGroup]:
    """Group findings that refer to the same issue across tools."""
    by_fp: dict[str, CorrelationGroup] = {}
    for f in findings:
        fp = f.fingerprint()
        group = by_fp.get(fp)
        if group is None:
            group = CorrelationGroup(fingerprint=fp)
            by_fp[fp] = group
        group.findings.append(f)
    return list(by_fp.values())


def merge_group(group: CorrelationGroup) -> Finding:
    """Collapse a group into a single representative finding."""
    # Highest severity wins, ties broken by highest confidence
    from .dedup import _SEVERITY_RANK
    best = sorted(
        group.findings,
        key=lambda f: (_SEVERITY_RANK.get(f.severity, 0), f.confidence),
        reverse=True,
    )[0]

    merged = Finding(
        title=best.title,
        severity=best.severity,
        confidence=max(f.confidence for f in group.findings),
        host=best.host,
        url=best.url,
        parameter=best.parameter,
        category=best.category,
        description=best.description,
        impact=best.impact,
        remediation=best.remediation,
        template_id=best.template_id,
        matched_at=best.matched_at,
        status="NEEDS_REVIEW" if len(group.findings) > 1 else best.status,
    )

    seen_evidence_keys: set[str] = set()
    for f in group.findings:
        for e in f.evidence:
            k = str(sorted(e.items())) if isinstance(e, dict) else str(e)
            if k not in seen_evidence_keys:
                seen_evidence_keys.add(k)
                merged.evidence.append(e)
        for r in f.references:
            if r not in merged.references:
                merged.references.append(r)
        for t in f.source_tools:
            if t not in merged.source_tools:
                merged.source_tools.append(t)

    merged.source_tools = sorted(merged.source_tools)
    return merged
