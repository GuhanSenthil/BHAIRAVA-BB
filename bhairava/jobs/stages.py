from __future__ import annotations

from enum import Enum


class JobStage(str, Enum):
    SCOPE = "scope"
    RECON = "recon"
    DISCOVERY = "discovery"
    ASSET_INTELLIGENCE = "asset_intelligence"
    DETECTION = "detection"
    CORRELATION = "correlation"
    EVIDENCE = "evidence"
    REVIEW = "review"
    REPORT = "report"
    COMPLETED = "completed"


STAGE_ORDER = [
    JobStage.SCOPE,
    JobStage.RECON,
    JobStage.DISCOVERY,
    JobStage.ASSET_INTELLIGENCE,
    JobStage.DETECTION,
    JobStage.CORRELATION,
    JobStage.EVIDENCE,
    JobStage.REVIEW,
    JobStage.REPORT,
    JobStage.COMPLETED,
]
