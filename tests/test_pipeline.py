"""tests for the pipeline engine."""

import pytest
import yaml

from bhairava.pipeline.engine import Pipeline, PipelineConfig


@pytest.fixture
def scope_file(tmp_path):
    p = tmp_path / "scope.yaml"
    p.write_text(yaml.safe_dump({
        "program": {"name": "Test Program"},
        "scope": {
            "domains": ["example.com"],
            "urls": ["https://example.com"],
            "excluded": [],
        },
        "limits": {"requests_per_second": 1, "max_concurrency": 1},
    }), encoding="utf-8")
    return p


def test_dry_run_no_filesystem(tmp_path, scope_file):
    cfg = PipelineConfig(
        scope_yaml=scope_file,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        dry_run=True,
    )
    pipe = Pipeline(cfg)
    result = pipe.run()
    assert result.job.target == "Test Program"
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "reports").exists()


def test_pipeline_creates_job(tmp_path, scope_file):
    cfg = PipelineConfig(
        scope_yaml=scope_file,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        stages=("scope",),
    )
    pipe = Pipeline(cfg)
    try:
        result = pipe.run()
        assert result.job.id.startswith("JOB-")
        assert result.job.status == "COMPLETED"
        assert "scope" in result.job.stages_run
    finally:
        pipe.close()


def test_resume_reuses_job(tmp_path, scope_file):
    data_dir = tmp_path / "data"

    cfg1 = PipelineConfig(
        scope_yaml=scope_file, data_dir=data_dir,
        reports_dir=tmp_path / "r1", stages=("scope",),
    )
    p1 = Pipeline(cfg1)
    try:
        r1 = p1.run()
        job_id = r1.job.id
    finally:
        p1.close()

    cfg2 = PipelineConfig(
        scope_yaml=scope_file, data_dir=data_dir,
        reports_dir=tmp_path / "r2", stages=("scope", "recon"),
        resume_job_id=job_id,
    )
    p2 = Pipeline(cfg2)
    try:
        class FakeReconResult:
            hosts = ["example.com"]
            errors = []
            sources = {"test": 1}

        class FakeReconEngine:
            def __init__(self, *args, **kwargs):
                pass

            def run(self, target, timeout=120):
                assert target == "example.com"
                return FakeReconResult()

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(
            "bhairava.pipeline.engine.ReconEngine",
            FakeReconEngine,
        )
        try:
            r2 = p2.run()
        finally:
            monkeypatch.undo()
        assert r2.job.id == job_id
        assert "scope" in r2.job.stages_run
        assert "recon" in r2.job.stages_run
    finally:
        p2.close()


def test_resume_unknown_job(tmp_path, scope_file):
    cfg = PipelineConfig(
        scope_yaml=scope_file, data_dir=tmp_path / "d",
        reports_dir=tmp_path / "r",
        resume_job_id="JOB-does-not-exist", stages=("scope",),
    )
    pipe = Pipeline(cfg)
    try:
        with pytest.raises(ValueError):
            pipe.run()
    finally:
        pipe.close()
