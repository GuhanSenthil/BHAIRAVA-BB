from __future__ import annotations

from pathlib import Path

import yaml

from .models import Plan

DEFAULT_STAGES = [
    "scope",
    "recon",
    "discovery",
    "asset_intelligence",
    "detection",
    "correlation",
    "evidence",
    "review",
    "report",
]


def create_plan(path: str | Path) -> Plan:
    path = Path(path)

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    scope = data.get("scope", {})
    limits = data.get("limits", {})
    tools = data.get("selected_tools", [])

    domains = scope.get("domains", [])
    urls = scope.get("urls", [])

    target = (
        urls[0]
        if urls
        else domains[0]
        if domains
        else "UNDEFINED"
    )

    return Plan(
        target=target,
        asset_count=len(domains) + len(urls),
        planned_tools=list(tools),
        requests_per_second=float(
            limits.get("requests_per_second", 0)
        ),
        max_concurrency=int(
            limits.get("max_concurrency", 1)
        ),
        stages=list(DEFAULT_STAGES),
    )
