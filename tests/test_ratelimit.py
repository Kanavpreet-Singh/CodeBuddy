import time

import pytest
from fastapi import HTTPException

from server.ratelimit import SlidingWindowLimiter


def test_allows_up_to_limit():
    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("user-a")  # should not raise


def test_blocks_over_limit_with_429():
    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("user-a")
    with pytest.raises(HTTPException) as exc:
        limiter.check("user-a")
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_keys_are_independent():
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=60)
    limiter.check("user-a")
    limiter.check("user-a")
    # user-b has its own budget
    limiter.check("user-b")
    limiter.check("user-b")
    with pytest.raises(HTTPException):
        limiter.check("user-a")


def test_window_resets_after_expiry():
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=1)
    limiter.check("user-a")
    limiter.check("user-a")
    with pytest.raises(HTTPException):
        limiter.check("user-a")
    time.sleep(1.1)  # let the window slide past the earlier hits
    limiter.check("user-a")  # should be allowed again
