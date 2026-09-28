"""SQLite persistence for Asset Intelligence."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Asset, AssetType, ScopeStatus


class AssetRepository:
    """Persist normalized assets in SQLite."""

    def __init__(self, database: str | Path) -> None:
        self.database = str(database)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    asset_type TEXT NOT NULL,
                    canonical_value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    parent_asset_id TEXT,
                    http_status INTEGER,
                    technologies_json TEXT NOT NULL,
                    scope_status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_assets_canonical
                ON assets(canonical_value)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_assets_parent
                ON assets(parent_asset_id)
                """
            )

    def upsert(self, asset: Asset) -> None:
        """Insert or update an asset."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assets (
                    asset_id,
                    asset_type,
                    canonical_value,
                    source,
                    first_seen,
                    last_seen,
                    parent_asset_id,
                    http_status,
                    technologies_json,
                    scope_status,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    source = excluded.source,
                    last_seen = excluded.last_seen,
                    parent_asset_id = COALESCE(
                        assets.parent_asset_id,
                        excluded.parent_asset_id
                    ),
                    http_status = COALESCE(
                        excluded.http_status,
                        assets.http_status
                    ),
                    technologies_json = excluded.technologies_json,
                    scope_status = excluded.scope_status,
                    metadata_json = excluded.metadata_json
                """,
                (
                    asset.asset_id,
                    asset.asset_type.value,
                    asset.canonical_value,
                    asset.source,
                    asset.first_seen,
                    asset.last_seen,
                    asset.parent_asset_id,
                    asset.http_status,
                    json.dumps(asset.technologies, sort_keys=True),
                    asset.scope_status.value,
                    json.dumps(asset.metadata, sort_keys=True),
                ),
            )

    def get(self, asset_id: str) -> Asset | None:
        """Retrieve an asset."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM assets WHERE asset_id = ?",
                (asset_id,),
            ).fetchone()

        if row is None:
            return None

        return Asset(
            asset_id=row["asset_id"],
            asset_type=AssetType(row["asset_type"]),
            canonical_value=row["canonical_value"],
            source=row["source"],
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            parent_asset_id=row["parent_asset_id"],
            http_status=row["http_status"],
            technologies=json.loads(row["technologies_json"]),
            scope_status=ScopeStatus(row["scope_status"]),
            metadata=json.loads(row["metadata_json"]),
        )

    def list(self) -> list[Asset]:
        """Return all assets."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM assets ORDER BY canonical_value"
            ).fetchall()

        return [
            Asset(
                asset_id=row["asset_id"],
                asset_type=AssetType(row["asset_type"]),
                canonical_value=row["canonical_value"],
                source=row["source"],
                first_seen=row["first_seen"],
                last_seen=row["last_seen"],
                parent_asset_id=row["parent_asset_id"],
                http_status=row["http_status"],
                technologies=json.loads(row["technologies_json"]),
                scope_status=ScopeStatus(row["scope_status"]),
                metadata=json.loads(row["metadata_json"]),
            )
            for row in rows
        ]
