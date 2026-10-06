"""BHAIRAVA-BB V7 Intelligence Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bhairava.assets.models import Asset
from bhairava.evidence.models import Evidence
from bhairava.findings.models import Finding, Observation

from .audit import AuditLog
from .correlation import UnifiedCorrelation, UnifiedCorrelationResult
from .evidence import EvidenceRelationshipStore
from .relationships import RelationshipGraph, RelationshipType


@dataclass
class IntelligenceResult:
    correlation: UnifiedCorrelationResult
    relationships: RelationshipGraph
    evidence_relationships: EvidenceRelationshipStore
    audit: AuditLog

    @property
    def findings(self) -> list[Finding]:
        return self.correlation.findings

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def observation_count(self) -> int:
        return self.correlation.observation_count

    @property
    def asset_count(self) -> int:
        return len(self.correlation.assets)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)


class IntelligenceEngine:
    """Combine existing V6/V7 primitives into one deterministic workflow.

    The engine only processes supplied data. It does not scan targets,
    execute commands, change scope, or confirm vulnerabilities.
    """

    def __init__(
        self,
        *,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.audit_log = audit_log or AuditLog()
        self.correlator = UnifiedCorrelation()

    def process(
        self,
        *,
        assets: Iterable[Asset] = (),
        observations: Iterable[Observation] = (),
        findings: Iterable[Finding] = (),
        evidence: Iterable[Evidence] = (),
    ) -> IntelligenceResult:
        assets = list(assets)
        observations = list(observations)
        findings = list(findings)
        evidence = list(evidence)

        correlation = self.correlator.correlate(
            observations,
            assets,
            findings,
        )

        graph = RelationshipGraph()
        evidence_relationships = EvidenceRelationshipStore()

        self._link_assets(
            graph,
            assets,
            observations,
            correlation.findings,
            evidence,
        )

        self._link_observations(
            graph,
            observations,
            correlation.findings,
            evidence,
        )

        self._link_evidence(
            graph,
            evidence_relationships,
            evidence,
            correlation.findings,
        )

        self.audit_log.record(
            "intelligence.process",
            "run",
            "v7",
            {
                "assets": len(assets),
                "observations": len(observations),
                "findings": len(correlation.findings),
                "evidence": len(evidence),
                "relationships": len(graph),
            },
        )

        return IntelligenceResult(
            correlation=correlation,
            relationships=graph,
            evidence_relationships=evidence_relationships,
            audit=self.audit_log,
        )

    @staticmethod
    def _link_assets(
        graph: RelationshipGraph,
        assets: list[Asset],
        observations: list[Observation],
        findings: list[Finding],
        evidence: list[Evidence],
    ) -> None:
        asset_by_value = {
            str(asset.canonical_value).lower().strip(): asset
            for asset in assets
        }

        for observation in observations:
            target = observation.target.lower().strip()

            for asset_value, asset in asset_by_value.items():
                if (
                    target == asset_value
                    or target.startswith(asset_value)
                    or asset_value.startswith(target)
                ):
                    graph.add(
                        asset.asset_id,
                        RelationshipType.ASSET_OBSERVATION,
                        observation.fingerprint(),
                    )

        for finding in findings:
            target = (
                finding.target
                or finding.host
                or finding.url
                or finding.endpoint
            ).lower().strip()

            for asset_value, asset in asset_by_value.items():
                if (
                    target == asset_value
                    or target.startswith(asset_value)
                    or asset_value.startswith(target)
                ):
                    graph.add(
                        asset.asset_id,
                        RelationshipType.ASSET_FINDING,
                        finding.finding_id or finding.id,
                    )

        for item in evidence:
            target = item.target.lower().strip()

            for asset_value, asset in asset_by_value.items():
                if (
                    target == asset_value
                    or target.startswith(asset_value)
                    or asset_value.startswith(target)
                ):
                    graph.add(
                        asset.asset_id,
                        RelationshipType.ASSET_EVIDENCE,
                        item.evidence_id,
                    )

    @staticmethod
    def _link_observations(
        graph: RelationshipGraph,
        observations: list[Observation],
        findings: list[Finding],
        evidence: list[Evidence],
    ) -> None:
        for finding in findings:
            finding_id = finding.finding_id or finding.id

            for observation in finding.observations:
                graph.add(
                    finding_id,
                    RelationshipType.FINDING_OBSERVATION,
                    observation.fingerprint(),
                )

        for item in evidence:
            for observation in observations:
                if (
                    item.target.strip().lower()
                    == observation.target.strip().lower()
                ):
                    graph.add(
                        observation.fingerprint(),
                        RelationshipType.OBSERVATION_EVIDENCE,
                        item.evidence_id,
                    )

    @staticmethod
    def _link_evidence(
        graph: RelationshipGraph,
        relationships: EvidenceRelationshipStore,
        evidence: list[Evidence],
        findings: list[Finding],
    ) -> None:
        findings_by_id = {
            finding.finding_id or finding.id: finding
            for finding in findings
        }

        for item in evidence:
            if not item.finding_id:
                continue

            # Evidence already contains its canonical finding_id.
            # Preserve that explicit relationship even when correlation
            # produces a merged representative finding.
            finding_id = item.finding_id

            graph.add(
                finding_id,
                RelationshipType.FINDING_EVIDENCE,
                item.evidence_id,
            )

            relationships.add(
                evidence_id=item.evidence_id,
                finding_id=finding_id,
                relation="supports",
            )

            # If the canonical finding is present, also attach the
            # evidence object to that finding without changing lifecycle.
            finding = findings_by_id.get(finding_id)
            if finding is not None and item not in finding.evidence:
                finding.evidence.append(item)
