"""bhairava.agent.providers.compatible -- OpenAI-compatible APIs.

Use for Groq, Together, Fireworks, vLLM, LM Studio, OpenRouter, etc.
Set endpoint + api_key_env + model in config.
"""
from __future__ import annotations

import json
import os
import urllib.request

from .base import AIProvider, ProviderError


class CompatibleProvider(AIProvider):
    name = "compatible"

    def _validate(self) -> None:
        if not self.config.endpoint:
            raise ProviderError("compatible provider requires 'endpoint'")
        if not self.config.model:
            raise ProviderError("compatible provider requires 'model'")
        api_key_env = self.config.api_key_env or "BHAIRAVA_AI_API_KEY"
        self.config.api_key_env = api_key_env
        if not self.config.api_key:
            self.config.api_key = os.environ.get(api_key_env, "")
        if not self.config.api_key:
            raise ProviderError(
                f"compatible provider requires API key via {api_key_env!r}"
            )

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
            raise ProviderError(f"compatible request failed: {e}") from e
        choices = data.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""
