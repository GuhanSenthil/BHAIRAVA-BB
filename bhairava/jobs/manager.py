"""bhairava.jobs.manager -- CRUD on jobs backed by SQLite."""
from __future__ import annotations

from ..storage.database import Database
from .models import Job


class JobManager:
    def __init__(self, db: Database):
        self.db = db

    def create(self, target: str, scope_yaml: str = "") -> Job:
        job = Job(target=target, scope_yaml=scope_yaml)
        self.save(job)
        return job

    def save(self, job: Job) -> None:
        row = job.to_row()
        cols = ",".join(row.keys())
        placeholders = ",".join("?" for _ in row)
        sql = f"INSERT OR REPLACE INTO jobs ({cols}) VALUES ({placeholders})"
        self.db.execute(sql, tuple(row.values()))

    def get(self, job_id: str) -> Job | None:
        row = self.db.query_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return Job.from_row(row) if row else None

    def list(self, limit: int = 50) -> list[Job]:
        rows = self.db.query_all(
            "SELECT * FROM jobs ORDER BY started_at DESC, id DESC LIMIT ?", (limit,)
        )
        return [Job.from_row(r) for r in rows]

    def delete(self, job_id: str) -> bool:
        row = self.db.query_one("SELECT id FROM jobs WHERE id = ?", (job_id,))
        if not row:
            return False
        self.db.execute("DELETE FROM findings  WHERE job_id = ?", (job_id,))
        self.db.execute("DELETE FROM evidence  WHERE job_id = ?", (job_id,))
        self.db.execute("DELETE FROM tool_runs WHERE job_id = ?", (job_id,))
        self.db.execute("DELETE FROM jobs      WHERE id     = ?", (job_id,))
        return True
