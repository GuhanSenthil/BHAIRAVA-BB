"""bhairava.agent.providers.google -- Google Gemini generateContent."""
from __future__ import annotations
import json
import urllib.request
from .base import AIProvider, ProviderError


DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-1.5-flash"


class GoogleProvider(AIProvider):
    name = "google"

    def _validate(self) -> None:
        if not self.config.endpoint:
            self.config.endpoint = DEFAULT_ENDPOINT
        if not self.config.model:
            self.config.model = DEFAULT_MODEL
        if not self.config.api_key_env:
            self.config.api_key_env = "GOOGLE_API_KEY"
            self.config.api_key = __import__("os").environ.get("GOOGLE_API_KEY", "") or \
                                   __import__("os").environ.get("GEMINI_API_KEY", "")
        super()._validate()

    def chat(self, system: str, user: str) -> str:
        url = self.config.endpoint.format(model=self.config.model)
        if "?" not in url:
            url += f"?key={self.config.api_key}"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            raise ProviderError(f"google request failed: {e}") from e
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts") or []
        return "".join(p.get("text", "") for p in parts if isinstance(p, dict))
