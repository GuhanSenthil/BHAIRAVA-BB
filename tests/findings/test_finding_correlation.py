from bhairava.findings import (
    FindingCorrelator,
    FindingState,
    Observation,
    calculate_confidence,
    deduplicate,
    transition,
)


def test_correlation_merges_multiple_sources():
    observations = [
        Observation(
            source="httpx",
            target="authorized.example",
            endpoint="/api/users",
            parameter="id",
            category="xss",
            title="Possible XSS",
        ),
        Observation(
            source="dalfox",
            target="authorized.example",
            endpoint="/api/users",
            parameter="id",
            category="xss",
            title="Possible XSS",
        ),
    ]

    findings = FindingCorrelator().correlate(observations)

    assert len(findings) == 1
    assert len(findings[0].observations) == 2
    assert findings[0].state == FindingState.NEEDS_REVIEW
    assert findings[0].confidence > 0


def test_confidence_increases_with_multiple_sources():
    observations = [
        Observation(
            source="httpx",
            target="authorized.example",
            endpoint="/test",
            category="test",
        ),
        Observation(
            source="nuclei",
            target="authorized.example",
            endpoint="/test",
            category="test",
        ),
    ]

    assert calculate_confidence(observations) > 0.1


def test_finding_deduplication():
    observations = [
        Observation(
            source="httpx",
            target="authorized.example",
            endpoint="/test",
            category="xss",
        ),
        Observation(
            source="nuclei",
            target="authorized.example",
            endpoint="/test",
            category="xss",
        ),
    ]

    findings = FindingCorrelator().correlate(observations)

    result = deduplicate(findings)

    assert len(result) == 1


def test_lifecycle_requires_review():
    observations = [
        Observation(
            source="nuclei",
            target="authorized.example",
            endpoint="/test",
            category="test",
        )
    ]

    finding = FindingCorrelator().correlate(observations)[0]

    assert finding.state == FindingState.NEEDS_REVIEW

    finding = transition(
        finding,
        FindingState.CONFIRMED,
    )

    assert finding.state == FindingState.CONFIRMED
