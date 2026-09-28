from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Plan:
    target: str
    asset_count: int = 0
    planned_tools: list[str] = field(default_factory=list)
    requests_per_second: float = 0.0
    max_concurrency: int = 1
    stages: list[str] = field(default_factory=list)
    authorization_required: bool = True

    def render(self) -> str:
        lines = [
            "=== BHAIRAVA-BB PLAN ===",
            f"Target: {self.target}",
            f"Assets: {self.asset_count}",
            f"Rate limit: {self.requests_per_second} requests/sec",
            f"Concurrency: {self.max_concurrency}",
            "",
            "Tools:",
        ]

        lines.extend(
            f"  - {tool}"
            for tool in self.planned_tools
        )

        lines.extend(
            [
                "",
                "Stages:",
            ]
        )

        lines.extend(
            f"  [ ] {stage}"
            for stage in self.stages
        )

        lines.extend(
            [
                "",
                "Authorization:",
                "  Active testing requires explicit authorization.",
                "  Scope and exclusions remain mandatory.",
                "  No network testing is performed by the planner.",
            ]
        )

        return "\n".join(lines)
