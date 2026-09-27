"""tests for sqlmap adapter safety."""
from bhairava.core.executor import ExecContext
from bhairava.tools.adapters.sqlmap import SqlmapAdapter


def test_default_safe_flags():
    a = SqlmapAdapter()
    cmd = a.build_command(ExecContext(target="https://x.test/p?id=1"))
    assert "--batch" in cmd
    assert "--smart" in cmd
    assert "--level" in cmd and "1" in cmd
    assert "--risk" in cmd and "1" in cmd


def test_blocks_os_shell():
    a = SqlmapAdapter()
    import pytest
    with pytest.raises(ValueError):
        a.build_command(ExecContext(target="x", extra_args=["--os-shell"]))


def test_blocks_file_read():
    a = SqlmapAdapter()
    import pytest
    with pytest.raises(ValueError):
        a.build_command(ExecContext(target="x", extra_args=["--file-read=/etc/passwd"]))


def test_blocks_dump():
    a = SqlmapAdapter()
    import pytest
    with pytest.raises(ValueError):
        a.build_command(ExecContext(target="x", extra_args=["--dump"]))


def test_parses_vulnerable_output():
    from bhairava.core.executor import ExecResult
    a = SqlmapAdapter()
    stdout = "Parameter: id (GET)\n    Type: boolean-based blind\n"
    rows = a.parse_output(ExecResult(tool="sqlmap", target="x", args=[],
                                     exit_code=0, stdout=stdout, stderr="",
                                     duration_ms=1))
    assert len(rows) == 1
    assert rows[0]["parameter"] == "id (GET)"
