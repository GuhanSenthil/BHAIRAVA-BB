from bhairava.assets.models import Asset, AssetType
from bhairava.evidence.models import Evidence
from bhairava.findings.models import Finding, FindingState, Observation
from bhairava.intelligence import (
    AuditLog,
    EvidenceRelationshipStore,
    IntelligenceEngine,
    RelationshipGraph,
    RelationshipType,
    UnifiedCorrelation,
)


def make_observation(source, target="example.com"):
    return Observation(
        source=source,
        target=target,
        endpoint=f"https://{target}/login",
        parameter="q",
        category="xss",
        title="Potential XSS",
    )


def test_relationship_graph():
    graph = RelationshipGraph()

    graph.add(
        "asset-1",
        RelationshipType.ASSET_FINDING,
        "finding-1",
    )

    graph.add(
        "finding-1",
        RelationshipType.FINDING_EVIDENCE,
        "evidence-1",
    )

    assert len(graph) == 2
    assert len(graph.outgoing("finding-1")) == 1
    assert len(graph.incoming("finding-1")) == 1


def test_evidence_relationship_store():
    store = EvidenceRelationshipStore()

    item = store.add(
        "evidence-1",
        "finding-1",
        asset_id="asset-1",
        relation="supports",
    )

    assert item.evidence_id == "evidence-1"
    assert item.finding_id == "finding-1"
    assert len(store) == 1
    assert len(store.for_finding("finding-1")) == 1


def test_unified_correlation_groups_same_observation():
    observations = [
        make_observation("nuclei"),
        make_observation("dalfox"),
    ]

    result = UnifiedCorrelation().correlate(observations)

    assert result.finding_count == 1
    assert result.observation_count == 2
    assert result.source_count == 2

    finding = result.findings[0]

    assert finding.state == FindingState.NEEDS_REVIEW
    assert finding.status == "NEEDS_REVIEW"
    assert finding.confidence > 0
    assert len(finding.observations) == 2


def test_unified_correlation_does_not_confirm():
    result = UnifiedCorrelation().correlate(
        [
            make_observation("nuclei"),
            make_observation("dalfox"),
        ]
    )

    assert result.findings[0].state == FindingState.NEEDS_REVIEW


def test_engine_creates_relationships():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    observation = make_observation("nuclei")

    result = IntelligenceEngine().process(
        assets=[asset],
        observations=[observation],
    )

    assert result.asset_count == 1
    assert result.observation_count == 1
    assert result.finding_count == 1
    assert result.relationship_count >= 2


def test_engine_links_existing_evidence():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    observation = make_observation("nuclei")

    finding = Finding(
        finding_id="finding-existing",
        target="example.com",
        endpoint="https://example.com/login",
        parameter="q",
        category="xss",
        title="Existing XSS",
        state=FindingState.NEEDS_REVIEW,
    )

    evidence = Evidence(
        evidence_id="evidence-1",
        finding_id="finding-existing",
        target="example.com",
        source="nuclei",
        tool_output="safe sanitized output",
    )

    result = IntelligenceEngine().process(
        assets=[asset],
        observations=[observation],
        findings=[finding],
        evidence=[evidence],
    )

    assert len(result.evidence_relationships) == 1
    assert result.evidence_relationships.for_finding(
        "finding-existing"
    )[0].evidence_id == "evidence-1"


def test_audit_log():
    audit = AuditLog()

    event = audit.record(
        "test",
        "finding",
        "finding-1",
        {"source": "test"},
    )

    assert event.action == "test"
    assert len(audit.all()) == 1


def test_engine_is_deterministic_for_same_observations():
    observations = [
        make_observation("nuclei"),
        make_observation("dalfox"),
    ]

    first = IntelligenceEngine().process(
        observations=observations,
    )

    second = IntelligenceEngine().process(
        observations=observations,
    )

    assert (
        first.findings[0].fingerprint()
        == second.findings[0].fingerprint()
    )

    assert (
        first.findings[0].confidence
        == second.findings[0].confidence
    )


def test_engine_handles_empty_input():
    result = IntelligenceEngine().process()

    assert result.asset_count == 0
    assert result.observation_count == 0
    assert result.finding_count == 0
    assert result.relationship_count == 0
