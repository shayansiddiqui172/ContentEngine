import time
import threading


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float):
        """rate: max requests per second."""
        self.rate = rate
        self.min_interval = 1.0 / rate
        self._last_call = 0.0
        self._lock = threading.Lock()

    def wait(self):
        """Block until a request is allowed."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last_call = time.monotonic()
