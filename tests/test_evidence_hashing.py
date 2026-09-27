"""tests for evidence hashing."""
from bhairava.evidence.hashing import canonical, evidence_hash, sha256_hex


def test_sha256_stable():
    a = sha256_hex("hello")
    b = sha256_hex("hello")
    assert a == b
    assert len(a) == 64


def test_evidence_hash_dict_order_independent():
    a = evidence_hash({"a": 1, "b": 2})
    b = evidence_hash({"b": 2, "a": 1})
    assert a == b


def test_evidence_hash_changes_with_content():
    a = evidence_hash({"x": 1})
    b = evidence_hash({"x": 2})
    assert a != b


def test_canonical_deterministic():
    assert canonical({"a": 1}) == canonical({"a": 1})
