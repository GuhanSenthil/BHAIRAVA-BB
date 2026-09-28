"""Technology fingerprinting from structured HTTP observations."""

from __future__ import annotations

from collections.abc import Mapping

HEADER_TECHNOLOGIES = {
    "server": {
        "nginx": "nginx",
        "apache": "apache",
        "caddy": "caddy",
        "gunicorn": "gunicorn",
        "iis": "iis",
    },
    "x-powered-by": {
        "php": "php",
        "express": "express",
        "asp.net": "asp.net",
        "django": "django",
    },
}


def fingerprint(
    *,
    headers: Mapping[str, str] | None = None,
    body: str = "",
    cookies: Mapping[str, str] | None = None,
) -> list[str]:
    """Return conservative technology observations.

    This function analyzes supplied observations only; it does not
    perform network requests.
    """
    found: set[str] = set()

    normalized_headers = {
        str(key).lower(): str(value).lower()
        for key, value in (headers or {}).items()
    }

    for header, signatures in HEADER_TECHNOLOGIES.items():
        value = normalized_headers.get(header, "")
        for signature, technology in signatures.items():
            if signature in value:
                found.add(technology)

    text = body.lower()

    body_signatures = {
        "wp-content": "wordpress",
        "drupal-settings-json": "drupal",
        "__next_data__": "next.js",
        "react": "react",
        "vue": "vue.js",
        "angular": "angular",
    }

    for signature, technology in body_signatures.items():
        if signature in text:
            found.add(technology)

    for cookie_name in (cookies or {}):
        cookie = cookie_name.lower()

        cookie_signatures = {
            "phpsessid": "php",
            "laravel_session": "laravel",
            "jsessionid": "java",
            "connect.sid": "express",
            "django": "django",
        }

        for signature, technology in cookie_signatures.items():
            if signature in cookie:
                found.add(technology)

    return sorted(found)
