"""bhairava.banner -- ASCII banner + colour helpers."""
from __future__ import annotations

import os
import sys

BANNER = r"""
 ██████╗ ██╗  ██╗ █████╗ ██╗██████╗  █████╗ ██╗   ██╗ █████╗
 ██╔══██╗██║  ██║██╔══██╗██║██╔══██╗██╔══██╗██║   ██║██╔══██╗
 ██████╔╝███████║███████║██║██████╔╝███████║██║   ██║███████║
 ██╔══██╗██╔══██║██╔══██║██║██╔══██╗██╔══██║╚██╗ ██╔╝██╔══██║
 ██████╔╝██║  ██║██║  ██║██║██║  ██║██║  ██║ ╚████╔╝ ██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═╝
"""

def _enable_utf8():
    if sys.platform == "win32":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleOutputCP(65001)
            k.SetConsoleCP(65001)
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _colors_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if "--no-color" in sys.argv:
        return False
    return sys.stdout.isatty() or os.environ.get("FORCE_COLOR")


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


def _c(code: str) -> str:
    return code if _colors_enabled() else ""


def print_banner(version: str = "1.0.0", show_help_hint: bool = True):
    _enable_utf8()
    print(_c(C.CYAN) + BANNER + _c(C.RESET))
    print(f" {_c(C.BOLD)}BHAIRAVA-BB v{version}{_c(C.RESET)}")
    print(f" {_c(C.DIM)}Authorized Bug Bounty Security Research Framework{_c(C.RESET)}")
    print()
    print(f" {_c(C.YELLOW)}[!]{_c(C.RESET)} Authorized targets only")
    print(f" {_c(C.YELLOW)}[!]{_c(C.RESET)} Scope Guard enforced")
    if show_help_hint:
        print()
        print(f" Usage: {_c(C.CYAN)}bhairava --help{_c(C.RESET)}")
    print()


def info(msg: str):     print(f"{_c(C.BLUE)}[*]{_c(C.RESET)} {msg}")
def success(msg: str):  print(f"{_c(C.GREEN)}[+]{_c(C.RESET)} {msg}")
def warn(msg: str):     print(f"{_c(C.YELLOW)}[!]{_c(C.RESET)} {msg}")
def error(msg: str):    print(f"{_c(C.RED)}[-]{_c(C.RESET)} {msg}", file=sys.stderr)
def blocked(msg: str):  print(f"{_c(C.RED)}[BLOCKED]{_c(C.RESET)} {msg}", file=sys.stderr)
