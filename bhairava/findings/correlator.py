from __future__ import annotations

import hashlib
from collections.abc import Iterable

from .confidence import calculate_confidence
from .models import Finding, FindingState, Observation


class FindingCorrelator:
    """
    Deterministic correlation only.

    Correlation aggregates observations. It does NOT independently
    confirm a vulnerability.
    """

    def correlate(self, observations: Iterable[Observation]) -> list[Finding]:
        groups: dict[str, list[Observation]] = {}

        for observation in observations:
            groups.setdefault(observation.fingerprint(), []).append(observation)

        findings: list[Finding] = []

        for fingerprint, group in groups.items():
            first = group[0]

            finding_id = (
                "finding_"
                + hashlib.sha256(fingerprint.encode()).hexdigest()[:24]
            )

            confidence = calculate_confidence(group)

            finding = Finding(
                finding_id=finding_id,
                target=first.target,
                endpoint=first.endpoint,
                parameter=first.parameter,
                category=first.category,
                title=first.title or "Correlated security observation",
                confidence=confidence,
                state=FindingState.NEEDS_REVIEW,
            )

            for observation in group:
                finding.add_observation(observation)

            finding.metadata["observation_count"] = len(group)
            finding.metadata["sources"] = sorted(
                {item.source for item in group}
            )

            findings.append(finding)

        return findings
