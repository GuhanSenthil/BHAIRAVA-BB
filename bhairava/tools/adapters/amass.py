"""amass adapter -- active/passive subdomain enumeration."""
from __future__ import annotations

from ...core.executor import ExecContext, ExecResult
from ..base import ToolAdapter


class AmassAdapter(ToolAdapter):
    name = "amass"
    description = "Subdomain enumeration (active + passive)"
    binary = "amass"

    def build_command(self, ctx: ExecContext) -> list[str]:
        # amass enum -passive -d <domain> -silent
        cmd = [self.binary, "enum", "-passive", "-d", ctx.target, "-silent"]
        if ctx.options.get("active"):
            cmd.remove("-passive")
            cmd += ["-active"]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        seen = set()
        for line in (result.stdout or "").splitlines():
            host = line.strip().lower()
            if host and host not in seen:
                seen.add(host)
                out.append({"host": host, "source": self.name})
        return out
