from __future__ import annotations

from .models import Finding


def deduplicate(findings: list[Finding]) -> list[Finding]:
    unique: dict[str, Finding] = {}

    for finding in findings:
        key = "|".join(
            [
                finding.target.lower().strip(),
                finding.endpoint.lower().strip(),
                finding.parameter.lower().strip(),
                finding.category.lower().strip(),
            ]
        )

        if key not in unique:
            unique[key] = finding
            continue

        existing = unique[key]

        for observation in finding.observations:
            existing.add_observation(observation)

        existing.confidence = max(
            existing.confidence,
            finding.confidence,
        )

    return list(unique.values())
