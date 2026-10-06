"""V7 unified deterministic correlation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from bhairava.assets.models import Asset
from bhairava.findings.confidence import calculate_confidence
from bhairava.findings.correlator import FindingCorrelator
from bhairava.findings.models import Finding, Observation


@dataclass
class UnifiedCorrelationResult:
    findings: list[Finding] = field(default_factory=list)
    observation_groups: dict[str, list[Observation]] = field(default_factory=dict)
    assets: list[Asset] = field(default_factory=list)

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def observation_count(self) -> int:
        return sum(len(items) for items in self.observation_groups.values())

    @property
    def source_count(self) -> int:
        sources: set[str] = set()

        for observations in self.observation_groups.values():
            sources.update(
                item.source.lower().strip()
                for item in observations
                if item.source
            )

        for finding in self.findings:
            sources.update(
                item.lower().strip()
                for item in finding.source_tools
                if item
            )

        return len(sources)


class UnifiedCorrelation:
    """Use existing Finding/Observation fingerprints as the canonical basis."""

    def __init__(self) -> None:
        self._finding_correlator = FindingCorrelator()

    @staticmethod
    def group_observations(
        observations: Iterable[Observation],
    ) -> dict[str, list[Observation]]:
        groups: dict[str, list[Observation]] = {}

        for observation in observations:
            fingerprint = observation.fingerprint()
            groups.setdefault(fingerprint, []).append(observation)

        return groups

    def correlate(
        self,
        observations: Iterable[Observation],
        assets: Iterable[Asset] = (),
        existing_findings: Iterable[Finding] = (),
    ) -> UnifiedCorrelationResult:
        observations = list(observations)
        assets = list(assets)
        existing_findings = list(existing_findings)

        groups = self.group_observations(observations)

        findings = self._finding_correlator.correlate(observations)

        # Existing findings are retained as observations of the existing
        # intelligence state. They are not automatically confirmed.
        if existing_findings:
            findings.extend(existing_findings)

        findings = self._deduplicate_findings(findings)

        for finding in findings:
            if finding.observations:
                finding.confidence = calculate_confidence(
                    finding.observations
                )

        return UnifiedCorrelationResult(
            findings=findings,
            observation_groups=groups,
            assets=assets,
        )

    @staticmethod
    def _deduplicate_findings(
        findings: list[Finding],
    ) -> list[Finding]:
        unique: dict[str, Finding] = {}

        for finding in findings:
            fingerprint = finding.fingerprint()

            if fingerprint not in unique:
                unique[fingerprint] = finding
                continue

            existing = unique[fingerprint]

            if finding.severity:
                severity_rank = {
                    "info": 0,
                    "low": 1,
                    "medium": 2,
                    "high": 3,
                    "critical": 4,
                }
                if severity_rank.get(finding.severity, 0) > severity_rank.get(
                    existing.severity,
                    0,
                ):
                    existing.severity = finding.severity

            existing.confidence = max(
                existing.confidence,
                finding.confidence,
            )

            for observation in finding.observations:
                if observation not in existing.observations:
                    existing.add_observation(observation)

            for evidence in finding.evidence:
                if evidence not in existing.evidence:
                    existing.evidence.append(evidence)

            for source in finding.source_tools:
                if source not in existing.source_tools:
                    existing.source_tools.append(source)

        return list(unique.values())
