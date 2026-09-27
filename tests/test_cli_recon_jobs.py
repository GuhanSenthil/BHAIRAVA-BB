from pathlib import Path
from types import SimpleNamespace

import pytest

from bhairava import cli
from bhairava.exceptions import ScopeViolation
from bhairava.jobs.manager import JobManager
from bhairava.storage.database import Database


def _args(tmp_path, scope_path):
    return SimpleNamespace(
        target="https://example.com",
        timeout=1,
        data_dir=str(tmp_path / "data"),
        scope=str(scope_path),
    )


def _write_scope(path):
    path.write_text(
        """
program:
  name: Test Program
scope:
  domains:
    - example.com
  urls:
    - https://example.com
  excluded: []
limits:
  requests_per_second: 5
  max_concurrency: 3
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_recon_cli_creates_completed_job(tmp_path, monkeypatch):
    scope = tmp_path / "scope.yaml"
    _write_scope(scope)

    class FakeResult:
        hosts = ["example.com"]
        sources = {"test": 1}
        errors = []
        skipped = []

    class FakeEngine:
        def __init__(self, *args):
            pass

        def run(self, target, timeout=120):
            return FakeResult()

    monkeypatch.setattr(cli, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "success", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "warn", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "error", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "bhairava.recon.engine.ReconEngine",
        FakeEngine,
    )

    args = _args(tmp_path, scope)

    assert cli._cmd_recon(args) == 0

    db_path = Path(args.data_dir) / "bhairava.db"

    with Database(db_path) as db:
        jobs = JobManager(db).list()

        assert len(jobs) == 1

        job = jobs[0]

        assert job.target == "https://example.com"
        assert job.status == "COMPLETED"
        assert job.stage == "recon"
        assert "recon" in job.stages_run
        assert job.stats["hosts"] == 1


def test_recon_cli_records_failed_job(tmp_path, monkeypatch):
    scope = tmp_path / "scope.yaml"
    _write_scope(scope)

    class FakeEngine:
        def __init__(self, *args):
            pass

        def run(self, target, timeout=120):
            raise RuntimeError("test recon failure")

    monkeypatch.setattr(cli, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "success", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "warn", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "error", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "bhairava.recon.engine.ReconEngine",
        FakeEngine,
    )

    args = _args(tmp_path, scope)

    assert cli._cmd_recon(args) == 1

    db_path = Path(args.data_dir) / "bhairava.db"

    with Database(db_path) as db:
        jobs = JobManager(db).list()

        assert len(jobs) == 1

        job = jobs[0]

        assert job.status == "FAILED"
        assert job.stage == "recon"
        assert "test recon failure" in job.error


def test_recon_cli_blocks_out_of_scope_before_job_creation(tmp_path):
    scope = tmp_path / "scope.yaml"
    _write_scope(scope)

    args = _args(tmp_path, scope)
    args.target = "https://not-example.com"

    with pytest.raises(ScopeViolation):
        cli._cmd_recon(args)

    db_path = Path(args.data_dir) / "bhairava.db"

    if db_path.exists():
        with Database(db_path) as db:
            assert JobManager(db).list() == []
