"""crt.sh source -- certificate transparency log lookup."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...scope_guard import ScopeGuard


CRTSH_URL = "https://crt.sh/?q={q}&output=json"


def query(domain: str, guard: "ScopeGuard | None" = None, timeout: int = 30) -> list[dict]:
    """Return list of {host, source} from certificate transparency logs.

    If guard is provided, the root domain is validated before the request.
    """
    if guard is not None:
        guard.validate_target(domain)

    q = urllib.parse.quote(f"%.{domain}", safe="")
    url = CRTSH_URL.format(q=q)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BHAIRAVA-BB/1.0 (authorized research)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception:
        return []

    try:
        rows = json.loads(body)
    except json.JSONDecodeError:
        return []

    seen = set()
    out = []
    for row in rows if isinstance(rows, list) else []:
        names = (row.get("name_value") or "") if isinstance(row, dict) else ""
        for name in str(names).splitlines():
            host = name.strip().lower().lstrip("*.").strip()
            if host and host not in seen and "." in host:
                seen.add(host)
                out.append({"host": host, "source": "crt.sh"})
    return out
