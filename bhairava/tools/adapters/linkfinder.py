"""linkfinder adapter -- extract endpoints from JavaScript."""
from __future__ import annotations

import re

from ...core.executor import ExecContext, ExecResult
from ..base import ToolAdapter


class LinkfinderAdapter(ToolAdapter):
    name = "linkfinder"
    description = "Extract endpoints from JavaScript files"
    binary = "linkfinder"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, "-i", ctx.target, "-o", "cli"]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if not line or line.startswith("["):
                continue
            # Filter to plausible endpoint-looking strings
            if re.match(r"^(https?://|/)[\w\-./?=&%]+$", line):
                out.append({"url": line, "source": self.name})
        return out
