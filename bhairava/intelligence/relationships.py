"""V7 relationship graph for assets, observations, findings and evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RelationshipType(StrEnum):
    ASSET_OBSERVATION = "asset_observation"
    ASSET_FINDING = "asset_finding"
    ASSET_EVIDENCE = "asset_evidence"
    FINDING_OBSERVATION = "finding_observation"
    FINDING_EVIDENCE = "finding_evidence"
    OBSERVATION_EVIDENCE = "observation_evidence"


@dataclass(frozen=True)
class Relationship:
    source_id: str
    relationship: RelationshipType
    target_id: str
    metadata: dict[str, object] = field(default_factory=dict)


class RelationshipGraph:
    """Deterministic in-memory relationship graph.

    This graph stores relationships only. It does not perform network
    operations and does not infer authorization.
    """

    def __init__(self) -> None:
        self._edges: dict[tuple[str, str, str], Relationship] = {}

    def add(
        self,
        source_id: str,
        relationship: RelationshipType | str,
        target_id: str,
        metadata: dict[str, object] | None = None,
    ) -> Relationship:
        relation = (
            relationship
            if isinstance(relationship, RelationshipType)
            else RelationshipType(str(relationship))
        )

        edge = Relationship(
            source_id=str(source_id),
            relationship=relation,
            target_id=str(target_id),
            metadata=dict(metadata or {}),
        )
        key = (
            edge.source_id,
            edge.relationship.value,
            edge.target_id,
        )
        self._edges[key] = edge
        return edge

    def all(self) -> list[Relationship]:
        return sorted(
            self._edges.values(),
            key=lambda item: (
                item.source_id,
                item.relationship.value,
                item.target_id,
            ),
        )

    def outgoing(self, source_id: str) -> list[Relationship]:
        return [
            edge for edge in self.all()
            if edge.source_id == source_id
        ]

    def incoming(self, target_id: str) -> list[Relationship]:
        return [
            edge for edge in self.all()
            if edge.target_id == target_id
        ]

    def related(self, entity_id: str) -> list[Relationship]:
        return [
            edge
            for edge in self.all()
            if edge.source_id == entity_id or edge.target_id == entity_id
        ]

    def __len__(self) -> int:
        return len(self._edges)
