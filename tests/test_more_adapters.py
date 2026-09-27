"""tests for the Phase B adapters."""
from bhairava.core.executor import ExecContext, ExecResult
from bhairava.tools.adapters.amass import AmassAdapter
from bhairava.tools.adapters.assetfinder import AssetfinderAdapter
from bhairava.tools.adapters.gau import GauAdapter
from bhairava.tools.adapters.waybackurls import WaybackurlsAdapter
from bhairava.tools.adapters.ffuf import FfufAdapter
from bhairava.tools.adapters.linkfinder import LinkfinderAdapter


def _res(tool, stdout):
    return ExecResult(tool=tool, target="t", args=[], exit_code=0,
                     stdout=stdout, stderr="", duration_ms=1)


def test_amass_builds_passive_command():
    a = AmassAdapter()
    cmd = a.build_command(ExecContext(target="example.com"))
    assert cmd[0] == "amass"
    assert "enum" in cmd
    assert "-passive" in cmd
    assert "example.com" in cmd


def test_amass_parse_dedupes():
    a = AmassAdapter()
    out = a.parse_output(_res("amass", "a.test\nb.test\na.test\n"))
    assert [r["host"] for r in out] == ["a.test", "b.test"]


def test_assetfinder_command():
    a = AssetfinderAdapter()
    cmd = a.build_command(ExecContext(target="example.com"))
    assert cmd == ["assetfinder", "--subs-only", "example.com"]


def test_gau_parse():
    a = GauAdapter()
    out = a.parse_output(_res("gau", "https://x.test/a\nnot-a-url\nhttps://x.test/b\n"))
    assert len(out) == 2


def test_waybackurls_parse():
    a = WaybackurlsAdapter()
    out = a.parse_output(_res("waybackurls", "https://x.test/p\n"))
    assert out[0]["url"] == "https://x.test/p"


def test_ffuf_requires_wordlist():
    a = FfufAdapter()
    with pytest.raises(ValueError):
        a.build_command(ExecContext(target="https://x.test"))


def test_ffuf_parse_json():
    a = FfufAdapter()
    line = '{"results":[{"url":"https://x.test/admin","status":200,"length":100,"words":5}]}'
    out = a.parse_output(_res("ffuf", line))
    assert out[0]["url"] == "https://x.test/admin"
    assert out[0]["status"] == 200


def test_linkfinder_parse():
    a = LinkfinderAdapter()
    out = a.parse_output(_res("linkfinder", "/api/v1/users\nhttps://x.test/x\ngarbage !!!\n"))
    urls = [r["url"] for r in out]
    assert "/api/v1/users" in urls
    assert "https://x.test/x" in urls


import pytest  # noqa: E402
