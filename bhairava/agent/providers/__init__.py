"""bhairava.agent.providers -- AI provider registry."""
from __future__ import annotations
from .base import AIProvider, ProviderError


def default_providers() -> dict[str, type[AIProvider]]:
    from .openai import OpenAIProvider
    from .anthropic import AnthropicProvider
    from .google import GoogleProvider
    from .ollama import OllamaProvider
    from .compatible import CompatibleProvider
    return {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "gemini": GoogleProvider,
        "ollama": OllamaProvider,
        "compatible": CompatibleProvider,
    }


def build_provider(cfg: dict) -> AIProvider:
    name = (cfg.get("provider") or "ollama").lower()
    providers = default_providers()
    cls = providers.get(name)
    if cls is None:
        raise ProviderError(f"unknown provider: {name!r}")
    return cls(cfg)
