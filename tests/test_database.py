"""tests for the SQLite backend."""
from pathlib import Path
from bhairava.storage.database import Database


def test_creates_file_and_schema(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    assert db_path.exists()
    row = db.query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
    assert row is not None
    db.close()


def test_migration_idempotent(tmp_path):
    p = tmp_path / "test.db"
    db1 = Database(p); db1.close()
    db2 = Database(p)
    rows = db2.query_all("SELECT version FROM schema_version")
    assert len(rows) == 1  # no re-apply
    db2.close()


def test_execute_and_query(tmp_path):
    db = Database(tmp_path / "t.db")
    db.execute("INSERT INTO jobs (id, target, status) VALUES (?,?,?)",
               ("J-1", "example.com", "CREATED"))
    row = db.query_one("SELECT * FROM jobs WHERE id = ?", ("J-1",))
    assert row["target"] == "example.com"
    db.close()
