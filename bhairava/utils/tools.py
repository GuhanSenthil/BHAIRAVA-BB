"""bhairava.utils.tools -- External tool discovery."""
from __future__ import annotations

import shutil

TOOLS = {
    "Reconnaissance": ["subfinder", "amass", "assetfinder"],
    "Discovery": ["httpx", "gau", "waybackurls", "ffuf"],
    "Detection": ["nuclei"],
    "Validation": ["dalfox", "xsstrike", "sqlmap", "zap-cli"],
}


def check_tools() -> list[tuple[str, bool]]:
    return [(name, shutil.which(name) is not None)
            for group in TOOLS.values() for name in group]


def render_tool_status(results: list[tuple[str, bool]]) -> str:
    lines = ["BHAIRAVA-BB TOOL STATUS", "=" * 44]
    i = 0
    for group, names in TOOLS.items():
        lines.append("")
        lines.append(f"  {group}")
        lines.append("")
        for name in names:
            found = results[i][1]
            mark = "OK " if found else "X  "
            state = "installed" if found else "not installed"
            lines.append(f"    {mark} {name:<14} {state}")
            i += 1
    lines.append("")
    lines.append("=" * 44)
    installed = sum(1 for _, ok in results if ok)
    missing = len(results) - installed
    lines.append(f"Available: {installed}")
    lines.append(f"Missing:   {missing}")
    return "\n".join(lines)
