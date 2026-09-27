"""nuclei adapter -- template-based vulnerability detection."""
from __future__ import annotations

import json as _json

from ...core.executor import ExecContext, ExecResult
from ..base import ToolAdapter


class NucleiAdapter(ToolAdapter):
    name = "nuclei"
    description = "Template-based vulnerability scanning"
    binary = "nuclei"

    def build_command(self, ctx: ExecContext) -> list[str]:
        cmd = [self.binary, "-u", ctx.target, "-silent", "-jsonl",
               "-no-color", "-stats=false"]
        severity = ctx.options.get("severity")
        if severity:
            cmd += ["-severity", ",".join(severity)]
        templates = ctx.options.get("templates")
        if templates:
            cmd += ["-t", ",".join(templates)]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                obj = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            info = obj.get("info") or {}
            out.append({
                "template_id": obj.get("template-id") or obj.get("templateID"),
                "name": info.get("name"),
                "severity": (info.get("severity") or "info").lower(),
                "host": obj.get("host"),
                "matched_at": obj.get("matched-at") or obj.get("matched"),
                "type": obj.get("type"),
                "source": self.name,
            })
        return out
