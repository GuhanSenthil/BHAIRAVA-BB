"""bhairava.agent.planner -- AI-suggested plan, policy-checked, scope-checked."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from ..exceptions import ScopeViolation
from ..scope_guard import ScopeGuard
from .policy import validate_plan
from .prompts import plan_prompt
from .providers import build_provider
from .providers.base import AIProvider, ProviderError


@dataclass
class PlanResult:
    steps: list[dict] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    raw_response: str = ""
    error: str | None = None


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "")
    # Greedy (outermost) match first, then progressively tighter.
    # This ensures we prefer {"steps":[...]} over the inner step objects.
    for pattern in (r"\{.*\}", r"\{.*?\}", r"\{[^{}]*\}"):
        for m in re.finditer(pattern, cleaned, re.DOTALL):
            try:
                obj = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
    return None


class Planner:
    """Wraps an AIProvider to produce policy- and scope-validated plans."""

    def __init__(self, ai_cfg: dict, guard: ScopeGuard):
        self.guard = guard
        self.cfg = ai_cfg or {}
        self.provider: AIProvider | None = None
        self._provider_error: str | None = None
        if self.cfg.get("enabled"):
            try:
                self.provider = build_provider(self.cfg)
            except ProviderError as e:
                self._provider_error = str(e)

    def available(self) -> bool:
        return self.provider is not None and self.provider.available()

    def plan(self, discovered: dict | None = None) -> PlanResult:
        result = PlanResult()
        if not self.cfg.get("enabled"):
            result.error = "AI disabled in config"
            return result
        if self.provider is None:
            result.error = self._provider_error or "provider unavailable"
            return result

        scope_summary = {
            "program": self.guard.scope.name,
            "domains": self.guard.scope.domains,
            "urls": self.guard.scope.urls,
            "excluded": self.guard.scope.excluded,
        }
        prompt = plan_prompt(scope_summary, discovered or {})

        try:
            raw = self.provider.chat(system="", user=prompt)
        except ProviderError as e:
            result.error = str(e)
            return result

        result.raw_response = raw
        plan_obj = _extract_json(raw)
        if plan_obj is None:
            result.error = "provider returned unparseable JSON"
            return result

        policy_report = validate_plan(plan_obj)
        for v in policy_report.rejected:
            result.rejected.append(f"step {v.step_index}: {v.reason}")

        # Now scope-check each accepted step
        for step in policy_report.accepted:
            try:
                self.guard.validate_target(step["target"])
                result.steps.append(step)
            except ScopeViolation:
                result.rejected.append(
                    f"step target out of scope: {step['target']}"
                )

        return result
