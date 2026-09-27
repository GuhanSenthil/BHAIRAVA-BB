"""bhairava.agent.providers.openai -- OpenAI chat completions."""
from __future__ import annotations

import json
import urllib.request

from .base import AIProvider, ProviderError

DEFAULT_ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(AIProvider):
    name = "openai"

    def _validate(self) -> None:
        if not self.config.endpoint:
            self.config.endpoint = DEFAULT_ENDPOINT
        if not self.config.model:
            self.config.model = DEFAULT_MODEL
        if not self.config.api_key_env:
            self.config.api_key_env = "OPENAI_API_KEY"
            self.config.api_key = __import__("os").environ.get("OPENAI_API_KEY", "")
        super()._validate()

    def chat(self, system: str, user: str) -> str:
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
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
            raise ProviderError(f"openai request failed: {e}") from e
        choices = data.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""
