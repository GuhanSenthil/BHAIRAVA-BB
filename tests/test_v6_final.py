from bhairava.findings import Observation
from bhairava.jobs import JobCheckpoint, JobStage
from bhairava.v6 import V6Pipeline


def test_v6_pipeline():
    checkpoint = JobCheckpoint(
        job_id="v6-test",
        stage=JobStage.CORRELATION,
        completed_stages=[
            "scope",
            "recon",
            "discovery",
            "asset_intelligence",
            "detection",
        ],
    )

    result = V6Pipeline().process(
        [
            Observation(
                source="httpx",
                target="authorized.example",
                endpoint="/api/users",
                parameter="id",
                category="xss",
                title="Possible XSS",
                evidence={"output": "safe observation"},
            ),
            Observation(
                source="dalfox",
                target="authorized.example",
                endpoint="/api/users",
                parameter="id",
                category="xss",
                title="Possible XSS",
                evidence={"output": "second observation"},
            ),
        ],
        checkpoint,
    )

    assert len(result.findings) == 1
    assert len(result.evidence) == 2
    assert result.resume_stage == JobStage.CORRELATION
