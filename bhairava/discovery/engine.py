"""bhairava.discovery.engine -- orchestrate discovery adapters."""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from ..core.executor import ExecContext, ToolExecutor
from ..exceptions import ScopeViolation
from ..tools.registry import ToolRegistry

DISCOVERY_ADAPTER_NAMES = ("httpx", "gau", "waybackurls")
ACTIVE_ADAPTER_NAMES = ("ffuf", "linkfinder")


@dataclass
class DiscoveryResult:
    target: str
    endpoints: list[dict] = field(default_factory=list)
    sources: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class DiscoveryEngine:
    def __init__(self, executor: ToolExecutor, registry: ToolRegistry, guard):
        self.executor = executor
        self.registry = registry
        self.guard = guard

    def run(self, target: str, timeout: int = 120, include_active: bool = False) -> DiscoveryResult:
        result = DiscoveryResult(target=target)

        try:
            self.guard.validate_target(target)
        except ScopeViolation as e:
            result.errors.append(f"scope violation: {e}")
            return result

        seen_urls: set[str] = set()
        names = DISCOVERY_ADAPTER_NAMES + (ACTIVE_ADAPTER_NAMES if include_active else ())

        for name in names:
            adapter = self.registry.get(name)
            if adapter is None:
                result.skipped.append(f"{name} (unknown)")
                continue
            if not adapter.available():
                result.skipped.append(f"{name} (not installed)")
                continue
            try:
                r = self.executor.run(adapter, ExecContext(target=target, timeout=timeout))
            except ValueError as e:
                result.errors.append(f"{name}: {e}")
                continue
            if not r.ok:
                result.errors.append(f"{name}: {r.error or r.exit_code}")
                continue
            try:
                rows = adapter.parse_output(r)
            except Exception as e:
                result.errors.append(f"{name} parse: {e}")
                continue
            count = 0
            for row in rows:
                url = (row.get("url") or "").strip()
                if not url or url in seen_urls:
                    continue
                if not url.startswith(("http://", "https://")):
                    continue
                try:
                    self.guard.validate_url(url)
                except ScopeViolation:
                    continue
                seen_urls.add(url)
                entry = dict(row)
                entry["host"] = urlparse(url).hostname or ""
                entry["path"] = urlparse(url).path
                entry["query"] = urlparse(url).query
                result.endpoints.append(entry)
                count += 1
            result.sources[name] = count

        return result
