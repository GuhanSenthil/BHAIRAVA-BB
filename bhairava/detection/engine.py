"""bhairava.detection.engine -- run Nuclei against scoped endpoints."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..core.executor import ExecContext, ToolExecutor
from ..exceptions import ScopeViolation
from ..findings.models import Finding
from ..tools.registry import ToolRegistry

DEFAULT_SEVERITIES = ("info", "low", "medium", "high", "critical")


@dataclass
class DetectionResult:
    target: str
    findings: list[Finding] = field(default_factory=list)
    raw_count: int = 0
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class DetectionEngine:
    def __init__(self, executor: ToolExecutor, registry: ToolRegistry, guard):
        self.executor = executor
        self.registry = registry
        self.guard = guard

    def run(
        self,
        target: str,
        severities: tuple[str, ...] = DEFAULT_SEVERITIES,
        templates: list[str] | None = None,
        timeout: int = 600,
        job_id: str = "",
    ) -> DetectionResult:
        result = DetectionResult(target=target)

        try:
            self.guard.validate_target(target)
        except ScopeViolation as e:
            result.errors.append(f"scope violation: {e}")
            return result

        adapter = self.registry.get("nuclei")
        if adapter is None:
            result.skipped.append("nuclei (unknown)")
            return result
        if not adapter.available():
            result.skipped.append("nuclei (not installed)")
            return result

        ctx = ExecContext(
            target=target,
            timeout=timeout,
            options={"severity": list(severities), "templates": templates or []},
        )
        r = self.executor.run(adapter, ctx)
        if not r.ok:
            result.errors.append(f"nuclei: {r.error or r.exit_code}")
            return result

        try:
            rows = adapter.parse_output(r)
        except Exception as e:
            result.errors.append(f"nuclei parse: {e}")
            return result

        result.raw_count = len(rows)

        for row in rows:
            matched = row.get("matched_at") or row.get("host") or target
            try:
                self.guard.validate_url(matched)
            except ScopeViolation:
                continue

            finding = Finding(
                title=row.get("name") or row.get("template_id") or "Nuclei finding",
                severity=row.get("severity") or "info",
                confidence=0.5,
                host=row.get("host") or "",
                url=matched,
                parameter="",
                category=(row.get("type") or "nuclei").lower(),
                description="",
                template_id=row.get("template_id") or "",
                matched_at=matched,
                source_tools=["nuclei"],
                status="CANDIDATE",
                job_id=job_id,
            )
            finding.evidence.append({
                "kind": "nuclei-template",
                "template_id": finding.template_id,
                "matched_at": matched,
            })
            result.findings.append(finding)

        return result
