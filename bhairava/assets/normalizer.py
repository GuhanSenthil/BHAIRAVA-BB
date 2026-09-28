"""Asset normalization utilities."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit, urlunsplit

from .models import AssetType


def normalize_domain(value: str) -> str:
    """Normalize a domain or hostname."""
    value = value.strip().lower().rstrip(".")
    if "://" in value:
        value = urlsplit(value).hostname or value
    return value.rstrip(".")


def normalize_url(value: str) -> str:
    """Normalize an HTTP(S) URL without changing its path semantics."""
    value = value.strip()

    if "://" not in value:
        value = f"https://{value}"

    parsed = urlsplit(value)

    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if not hostname:
        raise ValueError("URL does not contain a hostname")

    port = parsed.port

    if port is None:
        netloc = hostname
    elif (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    ):
        netloc = hostname
    else:
        netloc = f"{hostname}:{port}"

    path = parsed.path or "/"

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            parsed.query,
            "",
        )
    )


def detect_asset_type(value: str) -> AssetType:
    """Infer a conservative asset type from a value."""
    value = value.strip()

    try:
        ipaddress.ip_address(value)
        return AssetType.IP
    except ValueError:
        pass

    if "://" in value:
        parsed = urlsplit(value)
        if parsed.path and parsed.path != "/":
            return AssetType.ENDPOINT
        return AssetType.URL

    labels = normalize_domain(value).split(".")

    if len(labels) > 2:
        return AssetType.SUBDOMAIN

    return AssetType.DOMAIN


def canonicalize(value: str) -> tuple[AssetType, str]:
    """Return asset type and canonical representation."""
    asset_type = detect_asset_type(value)

    if asset_type in {
        AssetType.DOMAIN,
        AssetType.SUBDOMAIN,
    }:
        return asset_type, normalize_domain(value)

    if asset_type in {
        AssetType.URL,
        AssetType.ENDPOINT,
    }:
        return asset_type, normalize_url(value)

    return asset_type, value.strip().lower()
