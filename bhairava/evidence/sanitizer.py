"""bhairava.evidence.sanitizer -- redact secrets from evidence."""
from __future__ import annotations

import re
from typing import Any

REDACTED = "***REDACTED***"

_SENSITIVE_HEADERS = {
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "x-api-key", "x-auth-token", "x-csrf-token", "x-session-id",
}

_PATTERNS = [
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer " + REDACTED),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), REDACTED),
    (re.compile(r"\bsk-ant-[A-Za-z0-9\-]{20,}\b"), REDACTED),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), REDACTED),
    (re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"), REDACTED),
    (re.compile(r"\bAIza[0-9A-Za-z\-_]{30,}\b"), REDACTED),
]


def redact_value(value: str) -> str:
    if not isinstance(value, str):
        return value
    out = value
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out


def sanitize_headers(headers: dict) -> dict:
    out = {}
    for k, v in (headers or {}).items():
        if k.lower() in _SENSITIVE_HEADERS:
            out[k] = REDACTED
        else:
            out[k] = redact_value(str(v))
    return out


def sanitize_text(text: str, max_bytes: int = 4096) -> str:
    if not isinstance(text, str):
        return ""
    redacted = redact_value(text)
    if len(redacted) > max_bytes:
        redacted = redacted[:max_bytes] + "...[truncated]"
    return redacted


def sanitize(data: Any, max_bytes: int = 4096) -> Any:
    if isinstance(data, dict):
        return {k: sanitize(v, max_bytes) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize(x, max_bytes) for x in data]
    if isinstance(data, str):
        return sanitize_text(data, max_bytes)
    return data
