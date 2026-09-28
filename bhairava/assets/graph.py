"""Asset relationship graph."""

from __future__ import annotations

from collections import defaultdict

from .models import Asset


class AssetGraph:
    """In-memory parent/child relationship graph."""

    def __init__(self) -> None:
        self._assets: dict[str, Asset] = {}
        self._children: dict[str, set[str]] = defaultdict(set)

    def add(self, asset: Asset) -> None:
        """Add an asset and update its relationship."""
        self._assets[asset.asset_id] = asset

        if asset.parent_asset_id:
            self._children[asset.parent_asset_id].add(asset.asset_id)

    def get(self, asset_id: str) -> Asset | None:
        """Return an asset by ID."""
        return self._assets.get(asset_id)

    def children(self, asset_id: str) -> list[Asset]:
        """Return direct children in stable order."""
        ids = sorted(self._children.get(asset_id, set()))
        return [self._assets[item] for item in ids if item in self._assets]

    def roots(self) -> list[Asset]:
        """Return assets without a known parent."""
        return sorted(
            (
                asset
                for asset in self._assets.values()
                if asset.parent_asset_id is None
            ),
            key=lambda item: item.canonical_value,
        )

    def __len__(self) -> int:
        return len(self._assets)
