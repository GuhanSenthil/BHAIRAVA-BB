"""httpx adapter -- HTTP probe of discovered hosts."""
from __future__ import annotations
from ..base import ToolAdapter
from ...core.executor import ExecContext, ExecResult


class HttpxAdapter(ToolAdapter):
    name = "httpx"
    description = "HTTP probe / fingerprint live hosts"
    binary = "httpx"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, "-u", ctx.target, "-silent",
               "-status-code", "-title", "-tech-detect", "-server"]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            url = parts[0]
            code = None
            for p in parts[1:]:
                if p.startswith("[") and p.endswith("]"):
                    try:
                        code = int(p[1:-1])
                    except ValueError:
                        pass
            out.append({"url": url, "status_code": code, "source": self.name})
        return out
