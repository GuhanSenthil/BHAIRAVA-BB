"""tests for cross-tool correlation."""
from bhairava.findings.correlation import correlate, merge_group
from bhairava.findings.models import Finding


def test_correlate_groups_by_fingerprint():
    a = Finding(title="XSS", url="https://x.test/s", parameter="q", category="xss",
                severity="low", source_tools=["nuclei"])
    b = Finding(title="XSS-reflected", url="https://x.test/s", parameter="q",
                category="xss", severity="high", source_tools=["dalfox"])
    groups = correlate([a, b])
    assert len(groups) == 1
    assert set(groups[0].tools) == {"dalfox", "nuclei"}


def test_merge_group_picks_highest_severity():
    a = Finding(title="XSS", url="https://x.test/s", parameter="q", category="xss",
                severity="low", confidence=0.4, source_tools=["nuclei"])
    b = Finding(title="XSS-reflected", url="https://x.test/s", parameter="q",
                category="xss", severity="critical", confidence=0.6,
                source_tools=["dalfox"])
    merged = merge_group(correlate([a, b])[0])
    assert merged.severity == "critical"
    assert merged.confidence == 0.6
    assert merged.status == "NEEDS_REVIEW"
    assert set(merged.source_tools) == {"dalfox", "nuclei"}


def test_single_source_keeps_status():
    a = Finding(title="X", url="https://x.test/x", parameter="p", category="sqli",
                status="CANDIDATE", source_tools=["nuclei"])
    merged = merge_group(correlate([a])[0])
    assert merged.status == "CANDIDATE"
