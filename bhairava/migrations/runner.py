from __future__ import annotations

import sqlite3

MIGRATIONS = {
    1: """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
    """,

    2: """
        CREATE TABLE IF NOT EXISTS v6_assets (
            asset_id TEXT PRIMARY KEY,
            asset_type TEXT NOT NULL,
            canonical_value TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            http_status INTEGER,
            technologies TEXT NOT NULL DEFAULT '[]',
            scope_status TEXT NOT NULL DEFAULT 'UNKNOWN',
            metadata TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_v6_assets_type
        ON v6_assets(asset_type);
    """,

    3: """
        CREATE TABLE IF NOT EXISTS v6_findings (
            finding_id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            parameter TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            state TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_v6_findings_state
        ON v6_findings(state);
    """,

    4: """
        CREATE TABLE IF NOT EXISTS v6_evidence (
            evidence_id TEXT PRIMARY KEY,
            finding_id TEXT NOT NULL,
            target TEXT NOT NULL,
            source TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tool_output TEXT NOT NULL,
            request_metadata TEXT NOT NULL DEFAULT '{}',
            response_metadata TEXT NOT NULL DEFAULT '{}',
            reproduction TEXT NOT NULL DEFAULT '',
            confidence REAL NOT NULL DEFAULT 0,
            sha256 TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_v6_evidence_finding
        ON v6_evidence(finding_id);
    """,

    5: """
        CREATE TABLE IF NOT EXISTS v6_job_checkpoints (
            job_id TEXT PRIMARY KEY,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            completed_stages TEXT NOT NULL DEFAULT '[]',
            artifacts TEXT NOT NULL DEFAULT '{}',
            metadata TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );
    """,
}


def migrate(connection: sqlite3.Connection) -> int:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )

    current = connection.execute(
        "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
    ).fetchone()[0]

    applied = current

    for version in sorted(MIGRATIONS):
        if version <= current:
            continue

        connection.executescript(MIGRATIONS[version])

        from datetime import datetime, timezone

        connection.execute(
            """
            INSERT INTO schema_migrations(version, applied_at)
            VALUES (?, ?)
            """,
            (
                version,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        connection.commit()
        applied = version

    return applied
