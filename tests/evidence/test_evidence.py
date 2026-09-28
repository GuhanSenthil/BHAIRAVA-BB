from bhairava.evidence import (
    EvidenceCollector,
    sha256_text,
    verify_sha256,
)


def test_evidence_redacts_secrets():
    evidence = EvidenceCollector().collect(
        evidence_id="e1",
        finding_id="f1",
        target="authorized.example",
        source="test",
        tool_output=(
            "Authorization: Bearer SECRET123\n"
            "api_key=SUPERSECRET"
        ),
    )

    assert "SECRET123" not in evidence.tool_output
    assert "SUPERSECRET" not in evidence.tool_output
    assert "[REDACTED]" in evidence.tool_output


def test_evidence_integrity():
    value = "safe evidence"

    digest = sha256_text(value)

    assert verify_sha256(value, digest)
    assert not verify_sha256("modified", digest)


def test_evidence_has_hash():
    evidence = EvidenceCollector().collect(
        evidence_id="e1",
        finding_id="f1",
        target="authorized.example",
        source="test",
        tool_output="observation",
    )

    assert len(evidence.sha256) == 64
