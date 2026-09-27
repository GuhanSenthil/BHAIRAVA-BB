"""ffuf adapter -- content discovery (directory/file fuzzing)."""
from __future__ import annotations

import json as _json

from ...core.executor import ExecContext, ExecResult
from ..base import ToolAdapter


class FfufAdapter(ToolAdapter):
    name = "ffuf"
    description = "Content discovery via directory fuzzing"
    binary = "ffuf"

    def build_command(self, ctx: ExecContext) -> list[str]:
        wordlist = ctx.options.get("wordlist")
        if not wordlist:
            raise ValueError("ffuf requires options.wordlist")
        # Scope: base URL. ffuf appends FUZZ to the URL.
        url = ctx.target if "FUZZ" in ctx.target else ctx.target.rstrip("/") + "/FUZZ"
        cmd = [
            self.binary,
            "-u", url,
            "-w", str(wordlist),
            "-of", "json",
            "-o", "-",
            "-s",
        ]
        rate = ctx.options.get("rate")
        if rate:
            cmd += ["-rate", str(rate)]
        threads = ctx.options.get("threads")
        if threads:
            cmd += ["-t", str(threads)]
        cmd += ctx.extra_args
        return cmd

    def parse_output(self, result: ExecResult) -> list[dict]:
        out = []
        raw = (result.stdout or "").strip()
        if not raw.startswith("{"):
            return out
        try:
            data = _json.loads(raw)
        except _json.JSONDecodeError:
            return out
        for r in data.get("results", []) or []:
            out.append({
                "url": r.get("url"),
                "status": r.get("status"),
                "length": r.get("length"),
                "words": r.get("words"),
                "source": self.name,
            })
        return out
