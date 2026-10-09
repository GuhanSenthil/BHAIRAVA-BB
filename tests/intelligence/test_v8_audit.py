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
