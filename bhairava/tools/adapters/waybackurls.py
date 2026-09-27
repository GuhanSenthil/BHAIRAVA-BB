"""waybackurls adapter -- historical URLs from Wayback Machine."""
from __future__ import annotations
from ..base import ToolAdapter
from ...core.executor import ExecContext, ExecResult


class WaybackurlsAdapter(ToolAdapter):
    name = "waybackurls"
    description = "Historical URLs from Wayback Machine"
    binary = "waybackurls"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, ctx.target]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        for line in (result.stdout or "").splitlines():
            url = line.strip()
            if url.startswith(("http://", "https://")):
                out.append({"url": url, "source": self.name})
        return out
