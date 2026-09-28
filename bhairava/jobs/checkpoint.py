from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .stages import JobStage


@dataclass
class JobCheckpoint:
    job_id: str
    stage: JobStage
    status: str = "pending"
    completed_stages: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def complete(self, stage: JobStage) -> None:
        name = stage.value

        if name not in self.completed_stages:
            self.completed_stages.append(name)

        self.stage = stage
        self.status = "completed"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def can_resume_from(self, stage: JobStage) -> bool:
        return stage.value not in self.completed_stages
