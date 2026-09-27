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
    """Build the registry. Missing adapter modules are skipped, not fatal."""
    r = ToolRegistry()
    specs = [
        (".adapters.subfinder", "SubfinderAdapter"),
        (".adapters.amass", "AmassAdapter"),
        (".adapters.assetfinder", "AssetfinderAdapter"),
        (".adapters.httpx", "HttpxAdapter"),
        (".adapters.gau", "GauAdapter"),
        (".adapters.waybackurls", "WaybackurlsAdapter"),
        (".adapters.ffuf", "FfufAdapter"),
        (".adapters.linkfinder", "LinkfinderAdapter"),
        (".adapters.nuclei", "NucleiAdapter"),
        (".adapters.dalfox", "DalfoxAdapter"),
        (".adapters.sqlmap", "SqlmapAdapter"),
    ]
    import importlib
    for module_name, class_name in specs:
        try:
            mod = importlib.import_module(module_name, package=__package__)
            cls = getattr(mod, class_name)
            r.register(cls())
        except Exception:
            # Adapter module missing or broken -- skip it
            continue
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
