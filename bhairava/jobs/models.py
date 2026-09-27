"""bhairava.jobs.models -- Job dataclass and states."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

JOB_STATUSES = ("CREATED", "RUNNING", "PAUSED", "FAILED", "COMPLETED", "CANCELLED")

PIPELINE_STAGES = (
    "scope", "recon", "discovery", "detection",
    "validation", "evidence", "report",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_job_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"JOB-{stamp}-{uuid.uuid4().hex[:6]}"


@dataclass
class Job:
    id: str = field(default_factory=new_job_id)
    target: str = ""
    scope_yaml: str = ""
    status: str = "CREATED"
    stage: str = ""
    started_at: str = ""
    finished_at: str = ""
    stages_run: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    error: str = ""

    def __post_init__(self):
        if self.status not in JOB_STATUSES:
            self.status = "CREATED"

    def start(self) -> None:
        self.status = "RUNNING"
        self.started_at = self.started_at or _now()

    def finish(self) -> None:
        self.status = "COMPLETED"
        self.finished_at = _now()

    def fail(self, error: str) -> None:
        self.status = "FAILED"
        self.error = error
        self.finished_at = _now()

    def cancel(self) -> None:
        self.status = "CANCELLED"
        self.finished_at = _now()

    def mark_stage(self, stage: str) -> None:
        self.stage = stage
        if stage not in self.stages_run:
            self.stages_run.append(stage)

    def has_run(self, stage: str) -> bool:
        return stage in self.stages_run

    def to_row(self) -> dict:
        return {
            "id": self.id,
            "target": self.target,
            "scope_yaml": self.scope_yaml,
            "status": self.status,
            "stage": self.stage,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "stages_run": json.dumps(self.stages_run),
            "stats": json.dumps(self.stats),
            "error": self.error,
        }

    @classmethod
    def from_row(cls, row) -> "Job":
        return cls(
            id=row["id"],
            target=row["target"] or "",
            scope_yaml=row["scope_yaml"] or "",
            status=row["status"] or "CREATED",
            stage=row["stage"] or "",
            started_at=row["started_at"] or "",
            finished_at=row["finished_at"] or "",
            stages_run=json.loads(row["stages_run"] or "[]"),
            stats=json.loads(row["stats"] or "{}"),
            error=row["error"] or "",
        )
