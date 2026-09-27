"""dalfox adapter -- XSS validation."""
from __future__ import annotations

import json as _json

from ...core.executor import ExecContext, ExecResult
from ..base import ToolAdapter


class DalfoxAdapter(ToolAdapter):
    name = "dalfox"
    description = "XSS validation scanner"
    binary = "dalfox"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, "url", ctx.target,
               "--no-spinner", "--silence", "--format", "json"]
        if ctx.options.get("blind"):
            cmd += ["--blind", ctx.options["blind"]]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        raw = (result.stdout or "").strip()
        if not raw:
            return out
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            if obj.get("type") in ("V", "vulnerable") or obj.get("verified"):
                out.append({
                    "url": obj.get("data") or obj.get("url") or result.target,
                    "parameter": obj.get("param") or obj.get("parameter"),
                    "evidence": obj.get("evidence"),
                    "source": self.name,
                })
        return out
