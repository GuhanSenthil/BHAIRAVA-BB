"""bhairava.validation.approval -- human approval gate."""
from __future__ import annotations


def require_approval(action: str, target: str, auto_yes: bool = False) -> bool:
    if auto_yes:
        return True
    prompt = (
        f"\n[APPROVAL REQUIRED]\n"
        f"  action: {action}\n"
        f"  target: {target}\n"
        f"Proceed? [y/N] "
    )
    try:
        answer = input(prompt).strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")
