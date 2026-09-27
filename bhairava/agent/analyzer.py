"""bhairava.agent.analyzer -- AI-assisted analysis of findings."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..findings.models import Finding
from .policy import parse_analysis
from .prompts import analyze_finding_prompt
from .providers import build_provider
from .providers.base import AIProvider, ProviderError


@dataclass
class AnalysisResult:
    finding_id: str
    analysis: dict | None = None
    raw_response: str = ""
    error: str | None = None


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "")
    for pattern in (r"\{.*\}", r"\{.*?\}", r"\{[^{}]*\}"):
        for m in re.finditer(pattern, cleaned, re.DOTALL):
            try:
                obj = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
    return None


class Analyzer:
    def __init__(self, ai_cfg: dict):
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

    def analyze(self, finding: Finding) -> AnalysisResult:
        result = AnalysisResult(finding_id=finding.id)

        if not self.cfg.get("enabled"):
            result.error = "AI disabled"
            return result
        if self.provider is None:
            result.error = self._provider_error or "provider unavailable"
            return result

        # Only send safe fields -- never raw evidence bodies
        safe_finding = {
            "title": finding.title,
            "severity": finding.severity,
            "confidence": finding.confidence,
            "host": finding.host,
            "url": finding.url,
            "parameter": finding.parameter,
            "category": finding.category,
            "template_id": finding.template_id,
        }
        prompt = analyze_finding_prompt(safe_finding)

        try:
            raw = self.provider.chat(system="", user=prompt)
        except ProviderError as e:
            result.error = str(e)
            return result

        result.raw_response = raw
        parsed = _extract_json(raw)
        if parsed is None:
            result.error = "unparseable JSON"
            return result

        normalized = parse_analysis(parsed)
        if normalized is None:
            result.error = "failed schema validation"
            return result

        result.analysis = normalized
        return result

    def analyze_many(self, findings: list[Finding]) -> list[AnalysisResult]:
        return [self.analyze(f) for f in findings]
