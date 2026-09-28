from __future__ import annotations

import json
from pathlib import Path

from ..findings.models import Finding


def export_json(findings: list[Finding], path: str | Path) -> None:
    output = []

    for finding in findings:
        output.append(
            {
                "finding_id": finding.finding_id,
                "target": finding.target,
                "endpoint": finding.endpoint,
                "parameter": finding.parameter,
                "category": finding.category,
                "title": finding.title,
                "state": finding.state.value,
                "confidence": finding.confidence,
                "sources": sorted(
                    {
                        observation.source
                        for observation in finding.observations
                    }
                ),
                "observation_count": len(finding.observations),
            }
        )

    Path(path).write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )
