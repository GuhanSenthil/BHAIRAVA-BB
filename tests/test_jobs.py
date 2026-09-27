"""tests for job lifecycle."""

from bhairava.jobs.manager import JobManager
from bhairava.jobs.models import JOB_STATUSES, Job, new_job_id
from bhairava.storage.database import Database


def test_new_job_id_format():
    jid = new_job_id()
    assert jid.startswith("JOB-")
    assert len(jid) > 20


def test_job_lifecycle():
    j = Job(target="example.com")
    assert j.status == "CREATED"
    j.start()
    assert j.status == "RUNNING"
    j.mark_stage("recon")
    j.mark_stage("discovery")
    assert j.has_run("recon")
    assert not j.has_run("report")
    j.finish()
    assert j.status == "COMPLETED"
    assert j.finished_at


def test_job_fail():
    j = Job()
    j.start()
    j.fail("boom")
    assert j.status == "FAILED"
    assert j.error == "boom"


def test_manager_crud(tmp_path):
    db = Database(tmp_path / "t.db")
    mgr = JobManager(db)

    job = mgr.create("example.com", scope_yaml="scope.yaml")
    assert job.id.startswith("JOB-")

    fetched = mgr.get(job.id)
    assert fetched is not None
    assert fetched.target == "example.com"

    job.start()
    job.mark_stage("recon")
    job.stats["hosts"] = 5
    mgr.save(job)

    refetched = mgr.get(job.id)
    assert refetched.status == "RUNNING"
    assert "recon" in refetched.stages_run
    assert refetched.stats["hosts"] == 5

    listed = mgr.list()
    assert any(j.id == job.id for j in listed)

    assert mgr.delete(job.id) is True
    assert mgr.get(job.id) is None
    db.close()


def test_delete_missing_job(tmp_path):
    db = Database(tmp_path / "t.db")
    mgr = JobManager(db)
    assert mgr.delete("nope") is False
    db.close()


def test_status_validation():
    j = Job(status="BOGUS")
    assert j.status in JOB_STATUSES
    assert j.status == "CREATED"
