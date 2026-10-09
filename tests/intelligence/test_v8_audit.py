import json

from bhairava.intelligence.audit import AuditLog


def test_audit_log_persists_events(tmp_path):
    path = tmp_path / "audit.json"
    audit = AuditLog(path)

    audit.record("finding.reviewed", "finding", "finding-1", {"source": "manual"})
    saved = audit.save()

    assert saved == path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["action"] == "finding.reviewed"
    assert payload[0]["entity_id"] == "finding-1"


def test_audit_log_without_path_remains_in_memory():
    audit = AuditLog()

    audit.record("test", "finding", "finding-1")

    assert len(audit.all()) == 1
    assert audit.save() is None


def test_audit_log_does_not_persist_common_secrets(tmp_path):
    path = tmp_path / "audit.json"
    audit = AuditLog(path)

    audit.record(
        "tool.completed",
        "tool",
        "scanner-1",
        {
            "api_key": "secret-value",
            "authorization": "Bearer token-value",
            "summary": "completed",
        },
    )
    audit.save()

    content = path.read_text(encoding="utf-8")
    assert "secret-value" not in content
    assert "token-value" not in content
    assert "completed" in content


def test_audit_log_loads_saved_events(tmp_path):
    path = tmp_path / "audit.json"
    first = AuditLog(path)
    first.record(
        "finding.reviewed",
        "finding",
        "finding-2",
        {"api_key": "do-not-persist"},
    )
    first.save()

    second = AuditLog(path)

    assert len(second.all()) == 1
    assert second.all()[0].action == "finding.reviewed"
    assert second.all()[0].entity_id == "finding-2"
    assert second.all()[0].details["api_key"] == "[REDACTED]"


def test_audit_log_records_events_concurrently():
    from concurrent.futures import ThreadPoolExecutor

    audit = AuditLog()
    worker_count = 8
    events_per_worker = 100

    def record_events(worker_id):
        for index in range(events_per_worker):
            audit.record(
                "test.concurrent",
                "worker",
                f"{worker_id}-{index}",
            )

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        list(executor.map(record_events, range(worker_count)))

    events = audit.all()
    assert len(events) == worker_count * events_per_worker
    assert len({event.entity_id for event in events}) == len(events)


def test_audit_log_saves_concurrently_without_corrupting_json(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    audit = AuditLog(tmp_path / "audit.json")
    for index in range(100):
        audit.record("test.concurrent", "finding", f"finding-{index}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: audit.save(), range(16)))

    assert all(result == audit.path for result in results)
    payload = json.loads(audit.path.read_text(encoding="utf-8"))
    assert len(payload) == 100
    assert not list(tmp_path.glob(".audit.json.*.tmp"))


def test_audit_log_rejects_non_object_entries(tmp_path):
    path = tmp_path / "audit.json"
    path.write_text('[{"action":"test"}, "invalid-entry"]', encoding="utf-8")

    import pytest

    with pytest.raises(ValueError, match="Unable to load audit log"):
        AuditLog(path)


def test_audit_log_rejects_missing_required_fields(tmp_path):
    path = tmp_path / "audit.json"
    path.write_text(
        '[{"action":"test","entity_type":"finding","entity_id":"finding-1"}]',
        encoding="utf-8",
    )

    import pytest

    with pytest.raises(ValueError, match="Unable to load audit log"):
        AuditLog(path)


def test_audit_log_rejects_non_string_required_fields(tmp_path):
    import pytest

    path = tmp_path / "audit.json"
    path.write_text(
        json.dumps(
            [
                {
                    "action": 123,
                    "entity_type": "finding",
                    "entity_id": "finding-1",
                    "details": {},
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unable to load audit log"):
        AuditLog(path)


def test_audit_log_rejects_non_object_details(tmp_path):
    import pytest

    path = tmp_path / "audit.json"
    path.write_text(
        json.dumps(
            [
                {
                    "action": "test",
                    "entity_type": "finding",
                    "entity_id": "finding-1",
                    "details": ["unexpected"],
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unable to load audit log"):
        AuditLog(path)
