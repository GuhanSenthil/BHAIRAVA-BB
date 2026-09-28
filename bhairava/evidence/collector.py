"""bhairava.evidence.collector -- build evidence records for findings."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .hashing import evidence_hash
from .sanitizer import sanitize, sanitize_headers, sanitize_text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvidenceCollector:
    def __init__(self, max_preview_bytes: int = 4096):
        self.max_preview_bytes = max_preview_bytes

    def http_exchange(self, request: dict, response: dict,
                      tool: str = "", note: str = "") -> dict:
        req_headers = sanitize_headers(request.get("headers") or {})
        resp_headers = sanitize_headers(response.get("headers") or {})

        # Preserve the historical http_exchange() output contract.
        # sanitize_headers() uses [REDACTED], while this legacy
        # API exposes sensitive HTTP headers as ***REDACTED***.
        req_headers = {
            k: "***REDACTED***" if v == "[REDACTED]" else v
            for k, v in req_headers.items()
        }
        resp_headers = {
            k: "***REDACTED***" if v == "[REDACTED]" else v
            for k, v in resp_headers.items()
        }
        body_preview = sanitize(response.get("body_preview", ""),
                                self.max_preview_bytes)
        record = {
            "kind": "http-exchange",
            "timestamp": _now(),
            "tool": tool,
            "note": note,
            "request": {
                "method": request.get("method", "GET"),
                "url": request.get("url", ""),
                "headers": req_headers,
            },
            "response": {
                "status": response.get("status"),
                "headers": resp_headers,
                "body_preview": body_preview,
            },
        }
        record["hash"] = evidence_hash({
            "url": record["request"]["url"],
            "status": record["response"]["status"],
            "body_preview": body_preview,
        })
        return record

    def tool_output(self, tool: str, stdout: str, stderr: str = "",
                    exit_code: int = 0, note: str = "") -> dict:
        safe_stdout = sanitize(stdout, self.max_preview_bytes)
        safe_stderr = sanitize(stderr, self.max_preview_bytes)
        record = {
            "kind": "tool-output",
            "timestamp": _now(),
            "tool": tool,
            "note": note,
            "exit_code": exit_code,
            "stdout_preview": safe_stdout,
            "stderr_preview": safe_stderr,
        }
        record["hash"] = evidence_hash({
            "tool": tool, "stdout": safe_stdout, "exit_code": exit_code,
        })
        return record

    def collect(
        self,
        evidence_id: str,
        finding_id: str,
        target: str,
        source: str,
        tool_output: str = "",
        confidence: float = 0.0,
        note: str = "",
    ):
        """Create a V6 Evidence object with sanitized output and integrity hash."""
        from .models import Evidence

        sanitized_output = sanitize_text(
            tool_output,
            max_bytes=self.max_preview_bytes,
        )

        metadata = {
            "source": source,
        }

        if note:
            metadata["note"] = note

        digest_input = "|".join((
            evidence_id,
            finding_id,
            target,
            source,
            sanitized_output,
        ))

        digest = evidence_hash(digest_input)

        return Evidence(
            evidence_id=evidence_id,
            finding_id=finding_id,
            target=target,
            source=source,
            tool_output=sanitized_output,
            request_metadata=metadata,
            confidence=confidence,
            sha256=digest,
        )

    def custom(self, kind: str, payload: Any, note: str = "") -> dict:
        safe = sanitize(payload, self.max_preview_bytes)
        return {
            "kind": kind,
            "timestamp": _now(),
            "note": note,
            "payload": safe,
            "hash": evidence_hash(safe),
        }
