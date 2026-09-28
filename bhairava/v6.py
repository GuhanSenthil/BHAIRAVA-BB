from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .evidence import EvidenceCollector
from .findings import FindingCorrelator, Observation, deduplicate
from .jobs import JobCheckpoint, JobStage, resume_from


@dataclass
class V6Result:
    findings: list
    evidence: list
    resume_stage: JobStage


class V6Pipeline:
    """
    Deterministic v6 orchestration layer.

    This class consumes observations already produced by authorized
    upstream components. It does not perform network discovery,
    exploitation, or out-of-scope testing itself.
    """

    def __init__(self) -> None:
        self.correlator = FindingCorrelator()
        self.evidence_collector = EvidenceCollector()

    def process(
        self,
        observations: Iterable[Observation],
        checkpoint: JobCheckpoint,
    ) -> V6Result:

        observations = list(observations)

        findings = self.correlator.correlate(observations)
        findings = deduplicate(findings)

        evidence = []

        for finding in findings:
            for index, observation in enumerate(
                finding.observations,
                start=1,
            ):
                evidence.append(
                    self.evidence_collector.collect(
                        evidence_id=(
                            f"{finding.finding_id}-e{index}"
                        ),
                        finding_id=finding.finding_id,
                        target=finding.target,
                        source=observation.source,
                        tool_output=str(
                            observation.evidence.get(
                                "output",
                                "",
                            )
                        ),
                        confidence=finding.confidence,
                    )
                )

        return V6Result(
            findings=findings,
            evidence=evidence,
            resume_stage=resume_from(checkpoint),
        )
