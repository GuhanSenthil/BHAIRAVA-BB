"""tests for the findings model."""
from bhairava.findings.models import Finding


def test_fingerprint_stable_across_instances():
    a = Finding(title="X", url="https://x.test/a?p=1", parameter="p", category="xss")
    b = Finding(title="different", url="https://x.test/a?p=2", parameter="p", category="xss")
    assert a.fingerprint() == b.fingerprint()


def test_fingerprint_differs_by_param():
    a = Finding(title="X", url="https://x.test/a", parameter="p1", category="xss")
    b = Finding(title="X", url="https://x.test/a", parameter="p2", category="xss")
    assert a.fingerprint() != b.fingerprint()


def test_host_inferred_from_url():
    f = Finding(title="X", url="https://app.example.com/path")
    assert f.host == "app.example.com"


def test_invalid_severity_normalised():
    f = Finding(title="X", severity="MEGA")
    assert f.severity == "info"


def test_invalid_status_normalised():
    f = Finding(title="X", status="weird")
    assert f.status == "CANDIDATE"


def test_to_dict_has_fingerprint():
    f = Finding(title="X", url="https://x.test/p")
    d = f.to_dict()
    assert "fingerprint" in d and isinstance(d["fingerprint"], str)
