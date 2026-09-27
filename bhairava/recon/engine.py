"""bhairava.recon.engine -- orchestrate recon adapters."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..core.executor import ExecContext, ToolExecutor
from ..exceptions import ScopeViolation
from ..tools.http_sources import crtsh
from ..tools.registry import ToolRegistry

RECON_ADAPTER_NAMES = ("subfinder", "amass", "assetfinder")


@dataclass
class ReconResult:
    target: str
    hosts: list[str] = field(default_factory=list)
    sources: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class ReconEngine:
    def __init__(self, executor: ToolExecutor, registry: ToolRegistry, guard):
        self.executor = executor
        self.registry = registry
        self.guard = guard

    def run(self, target: str, timeout: int = 120) -> ReconResult:
        result = ReconResult(target=target)

        try:
            self.guard.validate_target(target)
        except ScopeViolation as e:
            result.errors.append(f"scope violation: {e}")
            return result

        seen: set[str] = set()

        # CLI adapters
        for name in RECON_ADAPTER_NAMES:
            adapter = self.registry.get(name)
            if adapter is None:
                result.skipped.append(f"{name} (unknown)")
                continue
            if not adapter.available():
                result.skipped.append(f"{name} (not installed)")
                continue
            r = self.executor.run(adapter, ExecContext(target=target, timeout=timeout))
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
                h = (row.get("host") or "").strip().lower()
                if not h or h in seen:
                    continue
                # Re-check scope on every discovered asset
                try:
                    self.guard.validate_target(h)
                except ScopeViolation:
                    continue
                seen.add(h)
                result.hosts.append(h)
                count += 1
            result.sources[name] = count

        # crt.sh (HTTP source)
        try:
            rows = crtsh.query(target, guard=self.guard)
            count = 0
            for row in rows:
                h = (row.get("host") or "").strip().lower()
                if not h or h in seen:
                    continue
                try:
                    self.guard.validate_target(h)
                except ScopeViolation:
                    continue
                seen.add(h)
                result.hosts.append(h)
                count += 1
            result.sources["crt.sh"] = count
        except Exception as e:
            result.errors.append(f"crt.sh: {e}")

        return result
