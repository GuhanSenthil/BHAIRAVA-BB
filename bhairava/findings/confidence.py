from __future__ import annotations

from collections.abc import Iterable

from .models import Observation

SOURCE_WEIGHTS = {
    "nuclei": 0.35,
    "dalfox": 0.35,
    "sqlmap": 0.35,
    "httpx": 0.10,
    "gau": 0.10,
    "waybackurls": 0.10,
    "ffuf": 0.15,
    "linkfinder": 0.10,
    "manual": 0.40,
}


def calculate_confidence(observations: Iterable[Observation]) -> float:
    observations = list(observations)

    if not observations:
        return 0.0

    unique_sources = {
        observation.source.lower().strip()
        for observation in observations
        if observation.source
    }

    score = sum(
        SOURCE_WEIGHTS.get(source, 0.05)
        for source in unique_sources
    )

    if len(unique_sources) >= 2:
        score += 0.10

    if len(unique_sources) >= 3:
        score += 0.10

    return min(round(score, 3), 0.99)
