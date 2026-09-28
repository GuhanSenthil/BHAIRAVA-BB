"""Asset deduplication."""

from __future__ import annotations

from collections.abc import Iterable

from .models import Asset


def deduplicate(assets: Iterable[Asset]) -> list[Asset]:
    """Deduplicate assets by stable asset ID.

    The first object is retained while later observations enrich
    technology and source information.
    """
    result: dict[str, Asset] = {}

    for asset in assets:
        existing = result.get(asset.asset_id)

        if existing is None:
            result[asset.asset_id] = asset
            continue

        existing.touch(asset.source)

        if asset.http_status is not None:
            existing.http_status = asset.http_status

        for technology in asset.technologies:
            existing.add_technology(technology)

        if existing.parent_asset_id is None:
            existing.parent_asset_id = asset.parent_asset_id

        existing.metadata.update(asset.metadata)

    return list(result.values())
