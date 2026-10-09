"""Persistent storage for intelligence relationships."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..storage.database import Database
from .relationships import Relationship, RelationshipType


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RelationshipRepository:
    """Persist relationship edges using the shared SQLite database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    @staticmethod
    def _normalize_type(value: RelationshipType | str) -> RelationshipType:
        if isinstance(value, RelationshipType):
            return value
        return RelationshipType(str(value))

    @staticmethod
    def _from_row(row) -> Relationship:
        return Relationship(
            source_id=row["source_id"],
            relationship=RelationshipType(row["relationship"]),
            target_id=row["target_id"],
            metadata=json.loads(row["metadata_json"]),
        )

    def add(
        self,
        source_id: str,
        relationship: RelationshipType | str,
        target_id: str,
        metadata: dict[str, object] | None = None,
    ) -> Relationship:
        """Insert an edge or update metadata for an existing edge."""
        source = str(source_id).strip()
        target = str(target_id).strip()
        if not source or not target:
            raise ValueError("source_id and target_id must not be empty")

        relation = self._normalize_type(relationship)
        normalized_metadata = dict(metadata or {})
        metadata_json = json.dumps(
            normalized_metadata,
            sort_keys=True,
            separators=(",", ":"),
        )
        timestamp = _now()

        self.db.execute(
            """
            INSERT INTO intelligence_relationships (
                source_id, relationship, target_id, metadata_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id, relationship, target_id) DO UPDATE SET
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at
            """,
            (
                source,
                relation.value,
                target,
                metadata_json,
                timestamp,
                timestamp,
            ),
        )
        return Relationship(
            source_id=source,
            relationship=relation,
            target_id=target,
            metadata=normalized_metadata,
        )

    def all(self) -> list[Relationship]:
        rows = self.db.query_all(
            """
            SELECT source_id, relationship, target_id, metadata_json
            FROM intelligence_relationships
            ORDER BY source_id, relationship, target_id
            """
        )
        return [self._from_row(row) for row in rows]

    def outgoing(self, source_id: str) -> list[Relationship]:
        rows = self.db.query_all(
            """
            SELECT source_id, relationship, target_id, metadata_json
            FROM intelligence_relationships
            WHERE source_id = ?
            ORDER BY source_id, relationship, target_id
            """,
            (str(source_id),),
        )
        return [self._from_row(row) for row in rows]

    def incoming(self, target_id: str) -> list[Relationship]:
        rows = self.db.query_all(
            """
            SELECT source_id, relationship, target_id, metadata_json
            FROM intelligence_relationships
            WHERE target_id = ?
            ORDER BY source_id, relationship, target_id
            """,
            (str(target_id),),
        )
        return [self._from_row(row) for row in rows]

    def related(self, entity_id: str) -> list[Relationship]:
        rows = self.db.query_all(
            """
            SELECT source_id, relationship, target_id, metadata_json
            FROM intelligence_relationships
            WHERE source_id = ? OR target_id = ?
            ORDER BY source_id, relationship, target_id
            """,
            (str(entity_id), str(entity_id)),
        )
        return [self._from_row(row) for row in rows]

    def __len__(self) -> int:
        row = self.db.query_one(
            "SELECT COUNT(*) AS count FROM intelligence_relationships"
        )
        return int(row["count"])
