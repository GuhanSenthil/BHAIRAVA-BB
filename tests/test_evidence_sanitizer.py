"""tests for evidence sanitization."""
from bhairava.evidence.sanitizer import (
    REDACTED,
    redact_value,
    sanitize,
    sanitize_headers,
    sanitize_text,
)


def test_redacts_bearer_token():
    out = redact_value("Authorization: Bearer abc.def.ghi")
    assert "abc.def.ghi" not in out
    assert "REDACTED" in out


def test_redacts_openai_key():
    out = redact_value("key=sk-abcdefghijklmnopqrstuvwxyz1234")
    assert "sk-abcdefghijklmnopqrstuvwxyz1234" not in out


def test_redacts_github_pat():
    out = redact_value("ghp_abcdefghijklmnopqrstuvwxyz0123456789")
    assert "ghp_" not in out or "REDACTED" in out


def test_sanitize_headers_redacts_cookie():
    h = {"Cookie": "session=abc123", "Content-Type": "text/html"}
    out = sanitize_headers(h)
    assert out["Cookie"] == REDACTED
    assert out["Content-Type"] == "text/html"


def test_sanitize_headers_redacts_authorization():
    h = {"Authorization": "Basic dXNlcjpwYXNz", "Host": "example.com"}
    out = sanitize_headers(h)
    assert out["Authorization"] == REDACTED
    assert out["Host"] == "example.com"


def test_sanitize_truncates_long_body():
    long = "A" * 10000
    out = sanitize_text(long, max_bytes=100)
    assert len(out) < 200
    assert "[truncated]" in out


def test_sanitize_recursive():
    data = {"outer": {"token": "sk-abcdefghijklmnopqrstuvwxyz1234"}}
    out = sanitize(data)
    assert "sk-abcdefghijklmnopqrstuvwxyz1234" not in str(out)


def test_sanitize_preserves_plain_data():
    assert sanitize_text("hello world") == "hello world"
