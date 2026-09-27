"""BHAIRAVA-BB first-run setup."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml


def normalize_scope(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Scope cannot be empty.")
    if "://" not in value:
        value = "https://" + value
    p = urlparse(value)
    if p.scheme not in {"http", "https"}:
        raise ValueError("Scope must use http:// or https://.")
    if not p.hostname:
        raise ValueError("Scope must contain a hostname.")
    return value.rstrip("/")


def create_scope(path: str = "config/scope.yaml"):
    print("\n" + "=" * 60 + "\n BHAIRAVA-BB FIRST-RUN AUTHORIZED SCOPE\n" + "=" * 60)
    print("\nOnly enter a target for which you have explicit authorization.\n")
    while True:
        try:
            target = normalize_scope(input("Authorized scope URL/domain: "))
            break
        except ValueError as e:
            print(f"[!] {e}")
    p = urlparse(target)
    host = p.hostname or ""
    sub = input("Include subdomains? [y/N]: ").strip().lower() == "y"
    raw = input("Excluded hosts, comma-separated [optional]: ").strip()
    excluded = [x.strip().lower() for x in raw.split(",") if x.strip()]
    name = (
        input(f"Program name [Authorized program - {host}]: ").strip()
        or f"Authorized program - {host}"
    )
    domains = [host]
    if sub:
        domains.append(f"*.{host}")
    data = {
        "program": {"name": name},
        "scope": {"domains": domains, "urls": [target], "excluded": excluded},
        "limits": {"requests_per_second": 5, "max_concurrency": 3},
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"\n[+] Scope saved: {path}")
    return Path(path)


def choose_tools(available: list[str]) -> list[str]:
    if not available:
        print("[-] No supported tools detected.")
        return []
    print("\n" + "=" * 60 + "\n BHAIRAVA-BB TOOL SELECTION\n" + "=" * 60)
    print("\n  1) Use ALL installed tools\n  2) Use ONE tool\n  3) Use MULTIPLE tools\n")
    while True:
        choice = input("Selection [1-3]: ").strip()
        if choice == "1":
            return list(available)
        if choice in {"2", "3"}:
            for i, n in enumerate(available, 1):
                print(f"  {i}) {n}")
            try:
                vals = (
                    input("Tool number(s): ").split(",")
                    if choice == "3"
                    else [input("Tool number: ")]
                )
                selected = []
                for v in vals:
                    n = available[int(v.strip()) - 1]
                    if n not in selected:
                        selected.append(n)
                if selected:
                    return selected
            except (ValueError, IndexError):
                pass
            print("[!] Invalid selection.")
        else:
            print("[!] Choose 1, 2, or 3.")


def save_tool_selection(path: str, selected: list[str]):
    p = Path(path)
    data = {}
    if p.exists():
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            data = {}
    data["selected_tools"] = selected
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def run_first_setup(
    scope_path="config/scope.yaml", config_path="config/config.yaml", available_tools=None
):
    if not Path(scope_path).exists():
        create_scope(scope_path)
    selected = choose_tools(available_tools or [])
    save_tool_selection(config_path, selected)
    print("\n[+] First-run setup complete.")
    print("[+] Selected tools:", ", ".join(selected) if selected else "none")
    return selected
