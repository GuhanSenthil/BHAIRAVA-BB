"""tests for the SQLite backend."""
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
    db1 = Database(p)
    db1.close()
    db2 = Database(p)
    rows = db2.query_all("SELECT version FROM schema_version")
    assert [row["version"] for row in rows] == [1, 2]  # no re-apply
    db2.close()


def test_execute_and_query(tmp_path):
    db = Database(tmp_path / "t.db")
    db.execute("INSERT INTO jobs (id, target, status) VALUES (?,?,?)",
               ("J-1", "example.com", "CREATED"))
    row = db.query_one("SELECT * FROM jobs WHERE id = ?", ("J-1",))
    assert row["target"] == "example.com"
    db.close()



def test_close_waits_for_active_database_operation(tmp_path):
    import threading

    db = Database(tmp_path / "thread-safe.db")
    operation_started = threading.Event()
    release_operation = threading.Event()
    close_finished = threading.Event()
    errors = []

    def active_operation():
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT 1")
                operation_started.set()
                if not release_operation.wait(timeout=2):
                    raise TimeoutError("Test did not release database operation")
        except Exception as exc:
            errors.append(exc)

    def close_database():
        try:
            db.close()
            close_finished.set()
        except Exception as exc:
            errors.append(exc)

    worker = threading.Thread(target=active_operation)
    worker.start()
    assert operation_started.wait(timeout=2)

    closer = threading.Thread(target=close_database)
    closer.start()

    try:
        assert not close_finished.wait(timeout=0.1)
    finally:
        release_operation.set()

    worker.join(timeout=2)
    closer.join(timeout=2)

    assert not worker.is_alive()
    assert not closer.is_alive()
    assert close_finished.is_set()
    assert not errors
