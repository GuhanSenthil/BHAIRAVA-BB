"""bhairava.agent.providers.ollama -- local Ollama /api/chat."""
from __future__ import annotations
import json
import urllib.request
from .base import AIProvider, ProviderError


DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "llama3.2"


class OllamaProvider(AIProvider):
    name = "ollama"

    def _validate(self) -> None:
        if not self.config.endpoint:
            self.config.endpoint = DEFAULT_ENDPOINT
        if not self.config.model:
            self.config.model = DEFAULT_MODEL
        # No API key required

    def available(self) -> bool:
        try:
            import urllib.request as u
            with u.urlopen("http://127.0.0.1:11434/api/tags", timeout=2):
                return True
        except Exception:
            return False

    def chat(self, system: str, user: str) -> str:
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 800},
        }
        req = urllib.request.Request(
            self.config.endpoint,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            raise ProviderError(f"ollama request failed: {e}") from e
        return data.get("message", {}).get("content", "") or ""
