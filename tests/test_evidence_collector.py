"""tests for evidence collector."""
from bhairava.evidence.collector import EvidenceCollector


def test_http_exchange_redacts_cookies():
    c = EvidenceCollector()
    rec = c.http_exchange(
        request={"method": "GET", "url": "https://x.test/p",
                 "headers": {"Cookie": "session=secret"}},
        response={"status": 200, "headers": {"Set-Cookie": "s=abc"}},
        tool="nuclei",
    )
    assert rec["request"]["headers"]["Cookie"] == "***REDACTED***"
    assert rec["response"]["headers"]["Set-Cookie"] == "***REDACTED***"
    assert rec["kind"] == "http-exchange"
    assert "hash" in rec


def test_tool_output_preview():
    c = EvidenceCollector()
    rec = c.tool_output("nuclei", stdout="result-1\nresult-2", exit_code=0)
    assert rec["kind"] == "tool-output"
    assert "result-1" in rec["stdout_preview"]
    assert "hash" in rec


def test_custom_evidence():
    c = EvidenceCollector()
    rec = c.custom("note", {"key": "value"}, note="manual observation")
    assert rec["kind"] == "note"
    assert rec["payload"]["key"] == "value"
