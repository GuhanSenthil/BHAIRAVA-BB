"""bhairava.agent.providers.anthropic -- Anthropic Messages API."""
from __future__ import annotations
import json
import urllib.request
from .base import AIProvider, ProviderError


DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-3-5-haiku-20241022"


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def _validate(self) -> None:
        if not self.config.endpoint:
            self.config.endpoint = DEFAULT_ENDPOINT
        if not self.config.model:
            self.config.model = DEFAULT_MODEL
        if not self.config.api_key_env:
            self.config.api_key_env = "ANTHROPIC_API_KEY"
            self.config.api_key = __import__("os").environ.get("ANTHROPIC_API_KEY", "")
        super()._validate()

    def chat(self, system: str, user: str) -> str:
        body = {
            "model": self.config.model,
            "max_tokens": 800,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
        }
        req = urllib.request.Request(
            self.config.endpoint,
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            raise ProviderError(f"anthropic request failed: {e}") from e
        blocks = data.get("content") or []
        return "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
