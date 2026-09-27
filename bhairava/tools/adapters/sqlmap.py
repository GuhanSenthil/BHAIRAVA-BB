"""sqlmap adapter -- SQL injection validation (safe mode)."""
from __future__ import annotations

from ...core.executor import ExecContext, ExecResult
from ..base import ToolAdapter


class SqlmapAdapter(ToolAdapter):
    name = "sqlmap"
    description = "SQL injection validation (safe mode)"
    binary = "sqlmap"

    FORBIDDEN = (
        "--os-shell", "--os-pwn", "--os-cmd", "--os-smbrelay",
        "--file-read", "--file-write", "--file-dest",
        "--sql-shell", "--sql-query",
        "--dump", "--dump-all",
        "--privileges", "--passwords",
    )

    def build_command(self, ctx: ExecContext) -> list[str]:
        extra = list(ctx.extra_args)
        for a in extra:
            for bad in self.FORBIDDEN:
                if a.startswith(bad):
                    raise ValueError(f"forbidden sqlmap flag: {bad}")

        cmd = [
            self.binary, "-u", ctx.target,
            "--batch", "--smart",
            "--level", "1", "--risk", "1",
            "--disable-coloring",
        ]
        cmd += extra
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        stdout = result.stdout or ""
        if "is vulnerable" in stdout.lower() or "Parameter:" in stdout:
            current = None
            for line in stdout.splitlines():
                ls = line.strip()
                if ls.startswith("Parameter:"):
                    current = ls.replace("Parameter:", "").strip()
                if "Type:" in ls and current:
                    out.append({
                        "url": result.target,
                        "parameter": current,
                        "type": ls.split("Type:", 1)[1].strip(),
                        "source": self.name,
                    })
        return out
