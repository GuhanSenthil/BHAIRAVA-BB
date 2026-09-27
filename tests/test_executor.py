"""tests/test_executor.py -- executor safety and adapter parsing."""
from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from bhairava.core.executor import ExecContext, ToolExecutor
from bhairava.core.rate_limiter import RateLimiter
from bhairava.scope_guard import Scope, ScopeGuard
from bhairava.tools.base import ToolAdapter


class FakeAdapter(ToolAdapter):
    name = "fake"
    description = "for tests"
    binary = "fake-bin"

    def build_command(self, ctx):
        return ["fake-bin", "run", ctx.target]

    def parse_output(self, result):
        return [{"line": line_item} for line_item in (result.stdout or "").splitlines() if line_item.strip()]


@pytest.fixture
def guard():
    return ScopeGuard(Scope(name="T", domains=["allowed.test"]))


@pytest.fixture
def adapter():
    return FakeAdapter()


def test_blocks_out_of_scope(guard, adapter):
    ex = ToolExecutor(guard)
    with mock.patch("bhairava.tools.base.shutil.which", return_value="/fake"):
        r = ex.run(adapter, ExecContext(target="https://evil.test"))
    assert r.error and "scope" in r.error.lower()
    assert r.exit_code == -1


def test_missing_binary(guard, adapter):
    ex = ToolExecutor(guard)
    with mock.patch("bhairava.tools.base.shutil.which", return_value=None):
        r = ex.run(adapter, ExecContext(target="https://allowed.test"))
    assert r.error and "not installed" in r.error.lower()


def test_successful_run(guard, adapter):
    ex = ToolExecutor(guard)
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="one\ntwo\n", stderr="")
    with mock.patch("bhairava.tools.base.shutil.which", return_value="/fake"), \
         mock.patch("bhairava.core.executor.subprocess.run", return_value=fake):
        r = ex.run(adapter, ExecContext(target="https://allowed.test"))
    assert r.ok
    assert r.exit_code == 0
    assert "one" in r.stdout


def test_timeout(guard, adapter):
    ex = ToolExecutor(guard, default_timeout=1)
    with mock.patch("bhairava.tools.base.shutil.which", return_value="/fake"), \
         mock.patch("bhairava.core.executor.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(cmd=[], timeout=1)):
        r = ex.run(adapter, ExecContext(target="https://allowed.test"))
    assert r.timed_out
    assert "timeout" in r.error.lower()


def test_output_truncation(guard, adapter):
    ex = ToolExecutor(guard, max_output_bytes=10)
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="A" * 100, stderr="")
    with mock.patch("bhairava.tools.base.shutil.which", return_value="/fake"), \
         mock.patch("bhairava.core.executor.subprocess.run", return_value=fake):
        r = ex.run(adapter, ExecContext(target="https://allowed.test"))
    assert r.truncated
    assert len(r.stdout) == 10


def test_rate_limiter_enforces_interval():
    rl = RateLimiter(100.0)  # 10ms between calls
    import time
    t0 = time.monotonic()
    for _ in range(5):
        rl.wait()
    elapsed = time.monotonic() - t0
    # 4 intervals between 5 calls, ~40ms, allow slack
    assert elapsed >= 0.030


def test_env_allowlist(guard, adapter):
    ex = ToolExecutor(guard, env_allowlist=("PATH",))
    captured = {}
    def fake_run(*a, **kw):
        captured["env"] = kw.get("env", {})
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    import os
    os.environ["BHAIRAVA_SECRET_TEST"] = "leak"
    with mock.patch("bhairava.tools.base.shutil.which", return_value="/fake"), \
         mock.patch("bhairava.core.executor.subprocess.run", side_effect=fake_run):
        ex.run(adapter, ExecContext(target="https://allowed.test"))
    assert "BHAIRAVA_SECRET_TEST" not in captured["env"]
    assert "PATH" in captured["env"]
