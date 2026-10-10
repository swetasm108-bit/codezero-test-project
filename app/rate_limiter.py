import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable, Deque, Dict, Tuple

from fastapi import HTTPException, Request, Response, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float,
                 clock: Callable[[], float] = time.monotonic):
        if max_requests < 1 or window_seconds <= 0:
            raise ValueError("max_requests must be >= 1 and window_seconds > 0")
        self.max_requests = max_requests
        self.window = window_seconds
        self._clock = clock
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> Tuple[bool, int, float]:
        now = self._clock()
        cutoff = now - self.window
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.max_requests:
                retry_after = hits[0] + self.window - now
                return False, 0, max(retry_after, 0.0)

            hits.append(now)
            return True, self.max_requests - len(hits), 0.0

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)


def _client_key(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"key:{api_key}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


def rate_limit(max_requests: int, window_seconds: float,
               clock: Callable[[], float] = time.monotonic):
    limiter = RateLimiter(max_requests, window_seconds, clock)

    async def dependency(request: Request, response: Response) -> None:
        allowed, remaining, retry_after = limiter.check(_client_key(request))
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
                headers={
                    "Retry-After": str(int(retry_after) + 1),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

    dependency.limiter = limiter
    return dependency