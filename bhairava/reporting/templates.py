from __future__ import annotations

from ..findings.models import Finding


def finding_summary(finding: Finding) -> str:
    sources = ", ".join(
        sorted(
            {
                observation.source
                for observation in finding.observations
            }
        )
    )

    return "\n".join(
        [
            f"Finding: {finding.finding_id}",
            f"Title: {finding.title}",
            f"Target: {finding.target}",
            f"Endpoint: {finding.endpoint}",
            f"Parameter: {finding.parameter}",
            f"Category: {finding.category}",
            f"State: {finding.state.value}",
            f"Confidence: {finding.confidence:.3f}",
            f"Sources: {sources}",
            "",
            "Human review is required before confirmation.",
        ]
    )
