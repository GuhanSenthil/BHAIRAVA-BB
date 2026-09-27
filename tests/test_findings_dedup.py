"""tests for deduplication."""
from bhairava.findings.dedup import dedupe
from bhairava.findings.models import Finding


def test_same_fingerprint_merges():
    a = Finding(title="A", url="https://x.test/p", parameter="q", category="xss",
                severity="low", confidence=0.3, source_tools=["nuclei"])
    b = Finding(title="B", url="https://x.test/p", parameter="q", category="xss",
                severity="high", confidence=0.9, source_tools=["dalfox"])
    out = dedupe([a, b])
    assert len(out) == 1
    assert out[0].severity == "high"
    assert out[0].confidence == 0.9
    assert set(out[0].source_tools) == {"nuclei", "dalfox"}


def test_different_fingerprints_kept():
    a = Finding(title="A", url="https://x.test/a", parameter="q", category="xss")
    b = Finding(title="B", url="https://x.test/b", parameter="q", category="xss")
    assert len(dedupe([a, b])) == 2


def test_merges_evidence_lists():
    a = Finding(title="A", url="https://x.test/p", parameter="q", category="xss",
                evidence=[{"id": 1}])
    b = Finding(title="B", url="https://x.test/p", parameter="q", category="xss",
                evidence=[{"id": 2}, {"id": 1}])
    out = dedupe([a, b])
    assert len(out[0].evidence) == 2
