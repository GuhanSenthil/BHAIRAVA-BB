from __future__ import annotations

from .checkpoint import JobCheckpoint
from .stages import STAGE_ORDER, JobStage


def next_stage(checkpoint: JobCheckpoint) -> JobStage:
    completed = set(checkpoint.completed_stages)

    for stage in STAGE_ORDER:
        if stage.value not in completed:
            return stage

    return JobStage.COMPLETED


def resume_from(checkpoint: JobCheckpoint) -> JobStage:
    return next_stage(checkpoint)
