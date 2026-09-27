from pathlib import Path

from bhairava.utils.tools import TOOLS, get_tool


def test_core_tool_count():
    assert len(TOOLS) == 11


def test_core_tool_names():
    assert {x.name for x in TOOLS} == {
        "subfinder",
        "amass",
        "assetfinder",
        "httpx",
        "gau",
        "waybackurls",
        "ffuf",
        "linkfinder",
        "nuclei",
        "dalfox",
        "sqlmap",
    }


def test_httpx_aliases():
    t = get_tool("httpx")
    assert "httpx" in t.commands
    assert "httpx-toolkit" in t.commands


def test_scope_example_exists():
    assert Path("config/scope.example.yaml").exists()
