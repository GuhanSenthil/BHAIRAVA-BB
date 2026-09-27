"""bhairava.core.rate_limiter -- token-bucket rate limiter."""
from __future__ import annotations
import threading
import time


class RateLimiter:
    """Enforces a minimum interval between calls, thread-safe."""

    def __init__(self, requests_per_second: float):
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._last_call = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self.min_interval - (now - self._last_call)
            if delay > 0:
                time.sleep(delay)
                now = time.monotonic()
            self._last_call = now

    def try_wait(self) -> bool:
        with self._lock:
            now = time.monotonic()
            if now - self._last_call >= self.min_interval:
                self._last_call = now
                return True
            return False
