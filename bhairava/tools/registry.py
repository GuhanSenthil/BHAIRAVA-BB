"""bhairava.tools.registry -- discoverable adapter registry."""
from __future__ import annotations
from .base import ToolAdapter


class ToolRegistry:
    def __init__(self):
        self._adapters: dict[str, ToolAdapter] = {}

    def register(self, adapter: ToolAdapter) -> None:
        if not adapter.name:
            raise ValueError("adapter must have a name")
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> ToolAdapter | None:
        return self._adapters.get(name)

    def require(self, name: str) -> ToolAdapter:
        a = self.get(name)
        if a is None:
            raise KeyError(f"unknown tool adapter: {name}")
        return a

    def all(self) -> list[ToolAdapter]:
        return list(self._adapters.values())

    def available(self) -> list[ToolAdapter]:
        return [a for a in self.all() if a.available()]

    def names(self) -> list[str]:
        return list(self._adapters.keys())


def default_registry() -> ToolRegistry:
    from .adapters.subfinder import SubfinderAdapter
    from .adapters.amass import AmassAdapter
    from .adapters.assetfinder import AssetfinderAdapter
    from .adapters.httpx import HttpxAdapter
    from .adapters.gau import GauAdapter
    from .adapters.waybackurls import WaybackurlsAdapter
    from .adapters.ffuf import FfufAdapter
    from .adapters.linkfinder import LinkfinderAdapter
    from .adapters.nuclei import NucleiAdapter
    r = ToolRegistry()
    r.register(SubfinderAdapter())
    r.register(AmassAdapter())
    r.register(AssetfinderAdapter())
    r.register(HttpxAdapter())
    r.register(GauAdapter())
    r.register(WaybackurlsAdapter())
    r.register(FfufAdapter())
    r.register(LinkfinderAdapter())
    r.register(NucleiAdapter())
    return r


def render_registry_status(reg: ToolRegistry) -> str:
    lines = ["BHAIRAVA-BB TOOL STATUS", "=" * 44, ""]
    for a in reg.all():
        mark = "OK " if a.available() else "X  "
        state = a.description if a.available() else "not installed"
        lines.append(f"  {mark} {a.name:<14} {state}")
    lines.append("")
    lines.append("=" * 44)
    avail = len(reg.available())
    total = len(reg.all())
    lines.append(f"Available: {avail}/{total}")
    return "\n".join(lines)
