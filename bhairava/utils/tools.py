"""BHAIRAVA-BB external tool discovery."""

from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    commands: tuple[str, ...]


TOOLS = (
    ToolSpec("subfinder", "Passive subdomain enumeration", ("subfinder",)),
    ToolSpec("amass", "Subdomain enumeration", ("amass",)),
    ToolSpec("assetfinder", "Passive asset discovery", ("assetfinder",)),
    ToolSpec("httpx", "HTTP probing and fingerprinting", ("httpx", "httpx-toolkit")),
    ToolSpec("gau", "Known URL discovery", ("gau",)),
    ToolSpec("waybackurls", "Wayback URL discovery", ("waybackurls",)),
    ToolSpec("ffuf", "Content discovery", ("ffuf",)),
    ToolSpec("linkfinder", "JavaScript endpoint discovery", ("linkfinder",)),
    ToolSpec("nuclei", "Template-based vulnerability detection", ("nuclei",)),
    ToolSpec("dalfox", "XSS analysis and validation", ("dalfox",)),
    ToolSpec("sqlmap", "SQL injection validation", ("sqlmap",)),
)


def executable(tool: ToolSpec) -> str | None:
    for command in tool.commands:
        path = shutil.which(command)
        if path:
            return path
    return None


def installed_tools() -> list[ToolSpec]:
    return [tool for tool in TOOLS if executable(tool)]


def missing_tools() -> list[ToolSpec]:
    return [tool for tool in TOOLS if executable(tool) is None]


def check_tools() -> list[tuple[str, bool]]:
    return [(tool.name, executable(tool) is not None) for tool in TOOLS]


def get_tool(name: str) -> ToolSpec:
    name = name.strip().lower()
    for tool in TOOLS:
        if tool.name == name:
            return tool
    raise ValueError(f"Unknown BHAIRAVA tool: {name}")


def render_tool_status(results=None) -> str:
    results = check_tools() if results is None else results
    lines = ["BHAIRAVA-BB TOOL STATUS", "=" * 44]
    for name, available in results:
        lines.append(
            f"  {'OK' if available else 'X':<2} {name:<14} {'installed' if available else 'not installed'}"
        )
    installed = sum(1 for _, ok in results if ok)
    total = len(results)
    lines.extend(
        ["", "=" * 44, f"Available: {installed}/{total}", f"Missing:   {total - installed}/{total}"]
    )
    return "\n".join(lines)
