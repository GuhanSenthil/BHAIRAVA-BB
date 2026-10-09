import pytest

from bhairava.intelligence import RelationshipRepository, RelationshipType
from bhairava.storage.database import Database


def test_relationship_migration_creates_table(tmp_path):
    db = Database(tmp_path / "migration.db")
    try:
        versions = db.query_all("SELECT version FROM schema_version ORDER BY version")
        assert [row["version"] for row in versions] == [1, 2]
        row = db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            ("intelligence_relationships",),
        )
        assert row is not None
    finally:
        db.close()


def test_relationship_persists_after_reopen(tmp_path):
    path = tmp_path / "relationships.db"
    db = Database(path)
    repository = RelationshipRepository(db)
    repository.add(
        "asset-1",
        RelationshipType.ASSET_FINDING,
        "finding-1",
        {"source": "test", "confidence": 0.8},
    )
    db.close()

    reopened = Database(path)
    try:
        repository = RelationshipRepository(reopened)
        edges = repository.related("asset-1")
        assert len(edges) == 1
        assert edges[0].source_id == "asset-1"
        assert edges[0].relationship == RelationshipType.ASSET_FINDING
        assert edges[0].target_id == "finding-1"
        assert edges[0].metadata == {"confidence": 0.8, "source": "test"}
    finally:
        reopened.close()


def test_duplicate_relationship_updates_metadata_without_duplicate_edge(tmp_path):
    db = Database(tmp_path / "duplicate.db")
    try:
        repository = RelationshipRepository(db)
        repository.add("finding-1", "finding_evidence", "evidence-1", {"v": 1})
        repository.add("finding-1", "finding_evidence", "evidence-1", {"v": 2})

        assert len(repository) == 1
        assert repository.outgoing("finding-1")[0].metadata == {"v": 2}
    finally:
        db.close()


def test_invalid_relationship_type_is_rejected(tmp_path):
    db = Database(tmp_path / "invalid.db")
    try:
        repository = RelationshipRepository(db)
        with pytest.raises(ValueError):
            repository.add("asset-1", "not-a-relationship", "finding-1")
    finally:
        db.close()


def test_empty_relationship_ids_are_rejected(tmp_path):
    db = Database(tmp_path / "empty.db")
    try:
        repository = RelationshipRepository(db)
        with pytest.raises(ValueError):
            repository.add("", RelationshipType.ASSET_FINDING, "finding-1")
        with pytest.raises(ValueError):
            repository.add("asset-1", RelationshipType.ASSET_FINDING, " ")
    finally:
        db.close()
