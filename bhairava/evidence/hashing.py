"""bhairava.evidence.hashing -- stable evidence fingerprints."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def evidence_hash(evidence: dict | list | str) -> str:
    if isinstance(evidence, str):
        return sha256_hex(evidence)
    return sha256_hex(canonical(evidence))
