"""V7 evidence relationship support."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceRelationship:
    evidence_id: str
    finding_id: str
    asset_id: str = ""
    observation_id: str = ""
    relation: str = "supports"
    metadata: dict[str, object] = field(default_factory=dict)


class EvidenceRelationshipStore:
    """Deterministic relationship store for existing Evidence records."""

    def __init__(self) -> None:
        self._records: dict[str, EvidenceRelationship] = {}

    def add(
        self,
        evidence_id: str,
        finding_id: str,
        *,
        asset_id: str = "",
        observation_id: str = "",
        relation: str = "supports",
        metadata: dict[str, object] | None = None,
    ) -> EvidenceRelationship:
        record = EvidenceRelationship(
            evidence_id=evidence_id,
            finding_id=finding_id,
            asset_id=asset_id,
            observation_id=observation_id,
            relation=relation,
            metadata=dict(metadata or {}),
        )

        key = "|".join(
            (
                evidence_id,
                finding_id,
                asset_id,
                observation_id,
                relation,
            )
        )
        self._records[key] = record
        return record

    def all(self) -> list[EvidenceRelationship]:
        return list(self._records.values())

    def for_finding(self, finding_id: str) -> list[EvidenceRelationship]:
        return [
            item
            for item in self._records.values()
            if item.finding_id == finding_id
        ]

    def for_evidence(self, evidence_id: str) -> list[EvidenceRelationship]:
        return [
            item
            for item in self._records.values()
            if item.evidence_id == evidence_id
        ]

    def __len__(self) -> int:
        return len(self._records)
