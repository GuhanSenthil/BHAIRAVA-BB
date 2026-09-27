"""bhairava.agent.providers.base -- AI provider ABC."""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderConfig:
    provider: str = "ollama"
    model: str = ""
    endpoint: str = ""
    timeout: int = 60
    api_key_env: str = ""
    api_key: str = ""
    extra: dict = field(default_factory=dict)


class AIProvider(ABC):
    """Minimal chat-completion interface. Each provider adapts to it."""

    name: str = ""

    def __init__(self, cfg: dict):
        self.config = self._parse_cfg(cfg)
        self._validate()

    def _parse_cfg(self, cfg: dict) -> ProviderConfig:
        provider = (cfg.get("provider") or self.name or "ollama").lower()
        api_key_env = cfg.get("api_key_env") or ""
        api_key = ""
        if api_key_env:
            api_key = os.environ.get(api_key_env, "")
        if not api_key and cfg.get("api_key"):
            api_key = cfg["api_key"]
        return ProviderConfig(
            provider=provider,
            model=cfg.get("model") or "",
            endpoint=cfg.get("endpoint") or "",
            timeout=int(cfg.get("timeout", 60)),
            api_key_env=api_key_env,
            api_key=api_key,
        )

    def _validate(self) -> None:
        if self.config.api_key_env and not self.config.api_key:
            raise ProviderError(
                f"provider {self.config.provider!r} requires "
                f"environment variable {self.config.api_key_env!r} to be set"
            )

    @abstractmethod
    def chat(self, system: str, user: str) -> str:
        """Return raw model output text."""

    def available(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<{type(self).__name__} model={self.config.model!r}>"
