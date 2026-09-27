"""bhairava.agent.policy -- validate AI output before it can influence action.

The AI never executes anything. It produces suggestions. Those suggestions
must pass THIS policy engine, then Scope Guard, then the executor.

AI cannot:
  - expand scope or remove exclusions
  - disable rate limits or safety checks
  - approve destructive actions
  - mark findings confirmed
  - execute shell commands
"""
from __future__ import annotations

from dataclasses import dataclass, field

ALLOWED_MODULES = {"recon", "discover", "scan", "validate", "report"}
ALLOWED_TOOLS = {
    "subfinder", "amass", "assetfinder",
    "httpx", "gau", "waybackurls", "linkfinder", "ffuf",
    "nuclei", "dalfox", "sqlmap",
}

FORBIDDEN_SUBSTRINGS = (
    "rm -rf", "curl ", "wget ", "bash ", "sh -c", "powershell",
    "sudo ", "/etc/passwd", "eval(", "exec(", "os.system",
    "shell=True", "&&", "||", ";",
)


@dataclass
class PolicyViolation:
    step_index: int
    reason: str
    step: dict = field(default_factory=dict)


@dataclass
class PolicyReport:
    accepted: list[dict] = field(default_factory=list)
    rejected: list[PolicyViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True  # policy always returns a report; caller decides


def _contains_forbidden(text: str) -> str | None:
    low = (text or "").lower()
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in low:
            return bad
    return None


def validate_plan(plan: dict) -> PolicyReport:
    """Validate an AI-generated plan. Returns accepted/rejected steps."""
    report = PolicyReport()

    if not isinstance(plan, dict):
        report.rejected.append(PolicyViolation(0, "plan is not a JSON object"))
        return report

    steps = plan.get("steps")
    if steps is None:
        report.rejected.append(PolicyViolation(0, "missing 'steps' key"))
        return report
    if not isinstance(steps, list):
        report.rejected.append(PolicyViolation(0, "'steps' must be a list"))
        return report

    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            report.rejected.append(PolicyViolation(i, "step is not an object", {}))
            continue

        module = str(step.get("module", "")).strip().lower()
        tool = str(step.get("tool", "")).strip().lower()
        target = str(step.get("target", "")).strip()
        reason = str(step.get("reason", "")).strip()

        if module not in ALLOWED_MODULES:
            report.rejected.append(PolicyViolation(
                i, f"module not allowed: {module!r}", step))
            continue

        if tool and tool not in ALLOWED_TOOLS:
            report.rejected.append(PolicyViolation(
                i, f"tool not allowed: {tool!r}", step))
            continue

        if not target:
            report.rejected.append(PolicyViolation(i, "missing target", step))
            continue

        # Check for shell metacharacters or obvious injection in target
        bad = _contains_forbidden(target) or _contains_forbidden(reason)
        if bad:
            report.rejected.append(PolicyViolation(
                i, f"forbidden substring {bad!r} in step", step))
            continue

        # Normalize and accept. Caller still must run ScopeGuard on `target`.
        report.accepted.append({
            "module": module,
            "tool": tool,
            "target": target,
            "reason": reason,
        })

    return report


def parse_analysis(analysis: dict) -> dict | None:
    """Validate an AI analysis response. Returns normalized dict or None."""
    if not isinstance(analysis, dict):
        return None
    sev = str(analysis.get("severity_assessment", "")).strip().lower()
    if sev not in ("info", "low", "medium", "high", "critical"):
        sev = "info"
    try:
        conf = float(analysis.get("confidence_adjust", 0.3))
    except (TypeError, ValueError):
        conf = 0.3
    conf = max(0.0, min(1.0, conf))

    steps = analysis.get("verification_steps") or []
    if not isinstance(steps, list):
        steps = []
    steps = [str(s)[:200] for s in steps[:6]]

    return {
        "severity_assessment": sev,
        "confidence_adjust": conf,
        "summary": str(analysis.get("summary", ""))[:400],
        "verification_steps": steps,
        "notes": str(analysis.get("notes", ""))[:400],
    }
