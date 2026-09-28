from bhairava.findings import (
    FindingCorrelator,
    Observation,
)
from bhairava.reporting.templates import finding_summary


def test_finding_report_contains_review_state():
    finding = FindingCorrelator().correlate(
        [
            Observation(
                source="nuclei",
                target="authorized.example",
                endpoint="/test",
                category="test",
                title="Test observation",
            )
        ]
    )[0]

    report = finding_summary(finding)

    assert finding.finding_id in report
    assert "NEEDS_REVIEW" in report
    assert "Human review" in report
