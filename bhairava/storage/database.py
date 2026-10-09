"""bhairava.storage.database -- SQLite backend."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .migrations import MIGRATIONS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str | Path = "data/bhairava.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._open()
        self._migrate()

    def _open(self) -> None:
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")

    def _migrate(self) -> None:
        cur = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        current = 0
        if cur.fetchone():
            row = self._conn.execute(
                "SELECT MAX(version) AS v FROM schema_version"
            ).fetchone()
            current = row["v"] or 0
        else:
            self._conn.execute(
                "CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT)"
            )
            self._conn.commit()

        for version, statements in MIGRATIONS:
            if version <= current:
                continue
            with self._lock:
                for stmt in statements:
                    self._conn.execute(stmt)
                self._conn.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (version, _now()),
                )
                self._conn.commit()

    @contextmanager
    def cursor(self):
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.cursor() as c:
            c.execute(sql, params)

    def query_one(self, sql: str, params: tuple = ()):
        with self.cursor() as c:
            c.execute(sql, params)
            return c.fetchone()

    def query_all(self, sql: str, params: tuple = ()):
        with self.cursor() as c:
            c.execute(sql, params)
            return c.fetchall()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
