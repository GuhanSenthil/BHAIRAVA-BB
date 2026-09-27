"""bhairava.core.executor -- safe subprocess execution."""
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..exceptions import ScopeViolation
from .rate_limiter import RateLimiter

if TYPE_CHECKING:
    from ..scope_guard import ScopeGuard
    from ..tools.base import ToolAdapter


@dataclass
class ExecContext:
    target: str
    timeout: int | None = None
    extra_args: list[str] = field(default_factory=list)
    options: dict = field(default_factory=dict)


@dataclass
class ExecResult:
    tool: str
    target: str
    args: list[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    truncated: bool = False
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.exit_code == 0 and not self.timed_out


_DEFAULT_ENV_ALLOWLIST = (
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT",
)


class ToolExecutor:
    def __init__(
        self,
        guard: "ScopeGuard",
        rate_limiter: RateLimiter | None = None,
        default_timeout: int = 120,
        max_output_bytes: int = 2_000_000,
        env_allowlist: tuple[str, ...] | None = None,
    ):
        self.guard = guard
        self.rate_limiter = rate_limiter
        self.default_timeout = default_timeout
        self.max_output_bytes = max_output_bytes
        self.env_allowlist = env_allowlist or _DEFAULT_ENV_ALLOWLIST

    def run(self, adapter: "ToolAdapter", ctx: ExecContext) -> ExecResult:
        t0 = time.monotonic()

        def fail(msg: str, args: list[str] | None = None) -> ExecResult:
            return ExecResult(
                tool=adapter.name, target=ctx.target, args=args or [],
                exit_code=-1, stdout="", stderr="",
                duration_ms=int((time.monotonic() - t0) * 1000),
                error=msg,
            )

        if not adapter.available():
            return fail(f"tool not installed: {adapter.binary}")

        try:
            self.guard.validate_target(ctx.target)
        except ScopeViolation as e:
            return fail(f"scope violation: {e}")

        if self.rate_limiter is not None:
            self.rate_limiter.wait()

        try:
            args = adapter.build_command(ctx)
        except Exception as e:
            return fail(f"build_command failed: {e}")
        if not isinstance(args, list) or not args:
            return fail("build_command must return a non-empty list")

        timeout = ctx.timeout or self.default_timeout
        env = {k: v for k, v in os.environ.items() if k in self.env_allowlist}

        try:
            proc = subprocess.run(
                args, capture_output=True, text=True,
                timeout=timeout, check=False, env=env,
            )
        except subprocess.TimeoutExpired:
            return ExecResult(
                tool=adapter.name, target=ctx.target, args=args,
                exit_code=-1, stdout="", stderr="",
                duration_ms=int((time.monotonic() - t0) * 1000),
                timed_out=True, error=f"timeout after {timeout}s",
            )
        except FileNotFoundError:
            return fail(f"binary not found: {adapter.binary}", args)
        except Exception as e:
            return fail(f"exec failed: {e}", args)

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        truncated = False
        if len(stdout) > self.max_output_bytes:
            stdout = stdout[:self.max_output_bytes]
            truncated = True
        if len(stderr) > self.max_output_bytes:
            stderr = stderr[:self.max_output_bytes]
            truncated = True

        return ExecResult(
            tool=adapter.name, target=ctx.target, args=args,
            exit_code=proc.returncode, stdout=stdout, stderr=stderr,
            duration_ms=int((time.monotonic() - t0) * 1000),
            truncated=truncated,
        )
