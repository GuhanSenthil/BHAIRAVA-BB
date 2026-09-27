"""assetfinder adapter -- quick passive subdomain discovery."""
from __future__ import annotations

from ...core.executor import ExecContext, ExecResult
from ..base import ToolAdapter


class AssetfinderAdapter(ToolAdapter):
    name = "assetfinder"
    description = "Passive subdomain discovery"
    binary = "assetfinder"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, "--subs-only", ctx.target]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        for line in (result.stdout or "").splitlines():
            host = line.strip().lower()
            if host and "." in host:
                out.append({"host": host, "source": self.name})
        return out
