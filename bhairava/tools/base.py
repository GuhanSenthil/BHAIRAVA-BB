"""bhairava.tools.base -- abstract adapter interface."""
from __future__ import annotations
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.executor import ExecContext, ExecResult


class ToolAdapter(ABC):
    name: str = ""
    description: str = ""
    binary: str = ""

    def available(self) -> bool:
        if not self.binary:
            return False
        return shutil.which(self.binary) is not None

    def version(self) -> str | None:
        if not self.available():
            return None
        try:
            r = subprocess.run(
                [self.binary, "--version"],
                capture_output=True, text=True, timeout=10, check=False,
            )
            lines = (r.stdout or r.stderr or "").strip().splitlines()
            return lines[0] if lines else None
        except Exception:
            return None

    @abstractmethod
    def build_command(self, ctx: "ExecContext") -> list[str]:
        """Return argv list. Never shell operators."""

    @abstractmethod
    def parse_output(self, result: "ExecResult") -> list[dict]:
        """Convert stdout into structured records."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
