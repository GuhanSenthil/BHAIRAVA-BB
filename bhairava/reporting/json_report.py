"""bhairava.reporting.json_report -- JSON report renderer."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..findings.models import Finding


def render(findings: list[Finding], target: str = "", program: str = "") -> str:
    payload = {
        "generator": "BHAIRAVA-BB",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "program": program,
        "target": target,
        "findings": [f.to_dict() for f in findings],
        "count": len(findings),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
