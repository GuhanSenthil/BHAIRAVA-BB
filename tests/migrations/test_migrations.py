import sqlite3

from bhairava.migrations import migrate


def test_migrations_reach_latest_version():
    connection = sqlite3.connect(":memory:")

    version = migrate(connection)

    assert version == 5

    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        )
    }

    assert "v6_assets" in tables
    assert "v6_findings" in tables
    assert "v6_evidence" in tables
    assert "v6_job_checkpoints" in tables


def test_migrations_are_idempotent():
    connection = sqlite3.connect(":memory:")

    assert migrate(connection) == 5
    assert migrate(connection) == 5
