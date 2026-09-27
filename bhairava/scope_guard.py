"""bhairava.scope_guard -- Mandatory authorization boundary.

Every active operation MUST call ScopeGuard.validate_target or
validate_url before executing. Out-of-scope targets raise ScopeViolation.
"""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None

from .exceptions import ConfigError, ScopeViolation

_DOMAIN_RE = re.compile(r"^(\*\.)?([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", re.I)


@dataclass
class Scope:
    name: str = "Unnamed"
    domains: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    requests_per_second: float = 5.0
    max_concurrency: int = 3


def _normalize_host(host: str) -> str:
    host = (host or "").strip().lower()
    if host.endswith("."):
        host = host[:-1]
    return host


def _wildcard_match(pattern: str, host: str) -> bool:
    pattern = _normalize_host(pattern)
    host = _normalize_host(host)
    if pattern.startswith("*."):
        suffix = pattern[2:]
        return host == suffix or host.endswith("." + suffix)
    return host == pattern


class ScopeGuard:
    def __init__(self, scope: Scope):
        self.scope = scope
        self.decisions: list[tuple[str, str]] = []

    # ---- loading -----------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> "ScopeGuard":
        if yaml is None:
            raise ConfigError("PyYAML is required to load scope files")
        p = Path(path)
        if not p.exists():
            raise ConfigError(f"scope file not found: {p}")
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception as e:
            raise ConfigError(f"could not parse {p}: {e}") from e

        program = (raw.get("program") or {}).get("name", "Unnamed")
        scope_d = raw.get("scope") or {}
        limits = raw.get("limits") or {}

        scope = Scope(
            name=program,
            domains=[str(x).strip().lower() for x in scope_d.get("domains", [])],
            urls=[str(x).strip().lower() for x in scope_d.get("urls", [])],
            excluded=[str(x).strip().lower() for x in scope_d.get("excluded", [])],
            requests_per_second=float(limits.get("requests_per_second", 5.0)),
            max_concurrency=int(limits.get("max_concurrency", 3)),
        )
        return cls(scope)

    # ---- public API --------------------------------------------------------
    def is_excluded(self, target: str) -> bool:
        host = _host_of(target)
        if not host:
            return True
        return any(_wildcard_match(x, host) for x in self.scope.excluded)

    def is_in_scope(self, target: str) -> bool:
        host = _host_of(target)
        if not host or self.is_excluded(target):
            return False
        for pat in self.scope.domains:
            if _wildcard_match(pat, host):
                return True
        for u in self.scope.urls:
            if _same_url(u, target):
                return True
        return False

    def validate_target(self, target: str) -> None:
        """Raise ScopeViolation if target is not explicitly authorized."""
        if not self.is_in_scope(target):
            self.decisions.append((target, "BLOCKED"))
            raise ScopeViolation(f"target is outside authorized scope: {target}")
        self.decisions.append((target, "ALLOWED"))

    def validate_url(self, url: str) -> None:
        if urlparse(url).scheme.lower() not in ("http", "https"):
            raise ScopeViolation(f"only http/https allowed: {url}")
        self.validate_target(url)

    def validate_many(self, targets: Iterable[str]) -> list[str]:
        ok: list[str] = []
        for t in targets:
            try:
                self.validate_target(t)
                ok.append(t)
            except ScopeViolation:
                continue
        return ok

    # ---- introspection -----------------------------------------------------
    def summary(self) -> dict:
        return {
            "program": self.scope.name,
            "domains": list(self.scope.domains),
            "urls": list(self.scope.urls),
            "excluded": list(self.scope.excluded),
            "requests_per_second": self.scope.requests_per_second,
            "max_concurrency": self.scope.max_concurrency,
            "decisions": list(self.decisions),
        }


def _host_of(target: str) -> str:
    if not target:
        return ""
    t = target.strip()
    if "://" in t:
        return _normalize_host(urlparse(t).hostname or "")
    # Try bare IP or host
    try:
        ipaddress.ip_address(t.split(":")[0])
        return _normalize_host(t.split(":")[0])
    except ValueError:
        pass
    return _normalize_host(t.split("/")[0].split(":")[0])


def _same_url(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return (pa.scheme.lower(), _normalize_host(pa.hostname or ""), pa.path.rstrip("/")) == \
           (pb.scheme.lower(), _normalize_host(pb.hostname or ""), pb.path.rstrip("/"))
