from bhairava.jobs import (
    JobCheckpoint,
    JobStage,
    next_stage,
    resume_from,
)


def test_resume_from_scope():
    checkpoint = JobCheckpoint(
        job_id="job1",
        stage=JobStage.RECON,
        completed_stages=["scope"],
    )

    assert resume_from(checkpoint) == JobStage.RECON
    assert next_stage(checkpoint) == JobStage.RECON


def test_completed_stages_are_not_repeated():
    checkpoint = JobCheckpoint(
        job_id="job1",
        stage=JobStage.DISCOVERY,
        completed_stages=[
            "scope",
            "recon",
            "discovery",
        ],
    )

    assert next_stage(checkpoint) == JobStage.ASSET_INTELLIGENCE
