import os
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException

from server.auth import get_current_user_id


class SlidingWindowLimiter:
    """In-memory per-key sliding-window rate limiter.

    Dependency-free and correct for a single event-loop instance (no await
    between the deque operations, so no locking is needed). A horizontally
    scaled deployment would back this with Redis instead; see the README.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.max_requests:
            retry_after = int(hits[0] + self.window_seconds - now) + 1
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)


def _limiter(max_env: str, window_env: str, default_max: int, default_window: int) -> SlidingWindowLimiter:
    return SlidingWindowLimiter(
        max_requests=int(os.environ.get(max_env, str(default_max))),
        window_seconds=int(os.environ.get(window_env, str(default_window))),
    )


_generation_limiter = _limiter("RATE_LIMIT_GENERATE_MAX", "RATE_LIMIT_GENERATE_WINDOW", 5, 60)
_run_limiter = _limiter("RATE_LIMIT_RUN_MAX", "RATE_LIMIT_RUN_WINDOW", 10, 60)


def rate_limit_generation(user_id: str = Depends(get_current_user_id)) -> str:
    _generation_limiter.check(user_id)
    return user_id


def rate_limit_run(user_id: str = Depends(get_current_user_id)) -> str:
    _run_limiter.check(user_id)
    return user_id
