"""bhairava.validation.engine -- controlled validation of findings."""
from __future__ import annotations
from dataclasses import dataclass, field

from ..core.executor import ExecContext, ToolExecutor
from ..exceptions import ScopeViolation
from ..findings.lifecycle import confirm, reject
from ..findings.models import Finding
from ..tools.registry import ToolRegistry
from .approval import require_approval


VALIDATORS = {
    "dalfox": {"xss"},
    "sqlmap": {"sqli"},
}

IMPACTFUL_CATEGORIES = {"sqli"}


@dataclass
class ValidationResult:
    finding_id: str
    validated: bool = False
    rejected: bool = False
    status_before: str = ""
    status_after: str = ""
    evidence: list[dict] = field(default_factory=list)
    error: str | None = None


class ValidationEngine:
    def __init__(self, executor: ToolExecutor, registry: ToolRegistry, guard,
                 auto_approve: bool = False):
        self.executor = executor
        self.registry = registry
        self.guard = guard
        self.auto_approve = auto_approve

    def _pick_validator(self, finding: Finding):
        for name, cats in VALIDATORS.items():
            if finding.category.lower() in cats:
                adapter = self.registry.get(name)
                if adapter and adapter.available():
                    return adapter
        return None

    def validate(self, finding: Finding, timeout: int = 300) -> ValidationResult:
        result = ValidationResult(finding_id=finding.id,
                                  status_before=finding.status)

        if finding.status not in ("CANDIDATE", "NEEDS_REVIEW"):
            result.error = f"finding in terminal state: {finding.status}"
            result.status_after = finding.status
            return result

        try:
            self.guard.validate_url(finding.url or finding.matched_at)
        except ScopeViolation as e:
            result.error = f"scope violation: {e}"
            reject(finding)
            result.rejected = True
            result.status_after = finding.status
            return result

        adapter = self._pick_validator(finding)
        if adapter is None:
            result.error = f"no validator available for category {finding.category!r}"
            result.status_after = finding.status
            return result

        if finding.category.lower() in IMPACTFUL_CATEGORIES:
            ok = require_approval(
                action=f"run {adapter.name} against {finding.url}",
                target=finding.url,
                auto_yes=self.auto_approve,
            )
            if not ok:
                result.error = "user declined approval"
                result.status_after = finding.status
                return result

        ctx = ExecContext(target=finding.url, timeout=timeout)
        run = self.executor.run(adapter, ctx)
        if not run.ok:
            result.error = f"{adapter.name}: {run.error or run.exit_code}"
            result.status_after = finding.status
            return result

        try:
            rows = adapter.parse_output(run)
        except Exception as e:
            result.error = f"parse failed: {e}"
            result.status_after = finding.status
            return result

        if rows:
            confirm(finding)
            result.validated = True
            result.evidence.append({
                "kind": "validator-output",
                "tool": adapter.name,
                "rows": rows[:5],
            })
        else:
            reject(finding)
            result.rejected = True

        result.status_after = finding.status
        return result

    def validate_many(self, findings: list[Finding],
                      timeout: int = 300) -> list[ValidationResult]:
        return [self.validate(f, timeout=timeout) for f in findings]
