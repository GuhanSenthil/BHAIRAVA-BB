"""gau adapter -- get URLs from archive sources."""
from __future__ import annotations
from ..base import ToolAdapter
from ...core.executor import ExecContext, ExecResult


class GauAdapter(ToolAdapter):
    name = "gau"
    description = "Fetch known URLs from archives"
    binary = "gau"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, "--subs", ctx.target]
        if ctx.options.get("no_subs"):
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
