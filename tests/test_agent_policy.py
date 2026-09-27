"""tests for AI output policy validation."""
from bhairava.agent.policy import parse_analysis, validate_plan


def test_accepts_valid_plan():
    plan = {"steps": [
        {"module": "discover", "tool": "httpx", "target": "app.example.com",
         "reason": "identify live services"},
    ]}
    r = validate_plan(plan)
    assert len(r.accepted) == 1
    assert r.accepted[0]["tool"] == "httpx"


def test_rejects_unknown_module():
    plan = {"steps": [
        {"module": "exploit", "tool": "sqlmap", "target": "app.example.com",
         "reason": "x"},
    ]}
    r = validate_plan(plan)
    assert len(r.accepted) == 0
    assert any("not allowed" in v.reason for v in r.rejected)


def test_rejects_unknown_tool():
    plan = {"steps": [
        {"module": "scan", "tool": "metasploit", "target": "app.example.com",
         "reason": "x"},
    ]}
    r = validate_plan(plan)
    assert len(r.accepted) == 0


def test_rejects_shell_metachars():
    plan = {"steps": [
        {"module": "scan", "tool": "nuclei",
         "target": "app.example.com; rm -rf /", "reason": "x"},
    ]}
    r = validate_plan(plan)
    assert len(r.accepted) == 0
    assert any("forbidden" in v.reason.lower() for v in r.rejected)


def test_rejects_pipe_injection():
    plan = {"steps": [
        {"module": "scan", "tool": "nuclei",
         "target": "app.example.com | curl evil", "reason": "x"},
    ]}
    r = validate_plan(plan)
    assert len(r.accepted) == 0


def test_rejects_non_list_steps():
    r = validate_plan({"steps": "do things"})
    assert len(r.accepted) == 0
    assert len(r.rejected) >= 1


def test_parse_analysis_normalizes():
    out = parse_analysis({
        "severity_assessment": "HIGH",
        "confidence_adjust": 1.5,
        "summary": "test",
        "verification_steps": ["one"],
        "notes": "x",
    })
    assert out["severity_assessment"] == "high"
    assert out["confidence_adjust"] == 1.0  # clamped


def test_parse_analysis_bad_severity():
    out = parse_analysis({"severity_assessment": "super-bad"})
    assert out["severity_assessment"] == "info"


def test_parse_analysis_missing_steps():
    out = parse_analysis({})
    assert out is not None
    assert out["verification_steps"] == []
