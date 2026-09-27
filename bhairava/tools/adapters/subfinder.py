"""subfinder adapter -- passive subdomain enumeration."""
from __future__ import annotations
from ..base import ToolAdapter
from ...core.executor import ExecContext, ExecResult


class SubfinderAdapter(ToolAdapter):
    name = "subfinder"
    description = "Passive subdomain enumeration"
    binary = "subfinder"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, "-d", ctx.target, "-silent"]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        for line in (result.stdout or "").splitlines():
            host = line.strip().lower()
            if host:
                out.append({"host": host, "source": self.name})
        return out
