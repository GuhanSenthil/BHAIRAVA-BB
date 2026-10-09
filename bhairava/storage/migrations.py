"""bhairava.storage.migrations -- SQLite schema migrations."""
from __future__ import annotations

SCHEMA_VERSION = 2

MIGRATIONS: list[tuple[int, list[str]]] = [
    (1, [
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            scope_yaml TEXT,
            status TEXT NOT NULL,
            stage TEXT DEFAULT '',
            started_at TEXT,
            finished_at TEXT,
            stages_run TEXT DEFAULT '[]',
            stats TEXT DEFAULT '{}',
            error TEXT DEFAULT ''
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
        """
        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_findings_job ON findings(job_id)",
        """
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            finding_id TEXT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_evidence_job ON evidence(job_id)",
        """
        CREATE TABLE IF NOT EXISTS tool_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            tool TEXT NOT NULL,
            target TEXT NOT NULL,
            exit_code INTEGER,
            duration_ms INTEGER,
            error TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_tool_runs_job ON tool_runs(job_id)",
    ]),
    (2, [
        """
        CREATE TABLE IF NOT EXISTS intelligence_relationships (
            source_id TEXT NOT NULL,
            relationship TEXT NOT NULL,
            target_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (source_id, relationship, target_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_intel_rel_source ON intelligence_relationships(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_intel_rel_target ON intelligence_relationships(target_id)",
        "CREATE INDEX IF NOT EXISTS idx_intel_rel_type ON intelligence_relationships(relationship)",
    ]),
]
