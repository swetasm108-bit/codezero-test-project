import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.rate_limiter import RateLimiter, rate_limit


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_allows_up_to_limit_then_blocks():
    clock = FakeClock()
    rl = RateLimiter(3, 10, clock)
    assert [rl.check("a")[0] for _ in range(3)] == [True, True, True]
    allowed, remaining, retry = rl.check("a")
    assert not allowed and remaining == 0 and retry == pytest.approx(10)


def test_window_slides():
    clock = FakeClock()
    rl = RateLimiter(2, 10, clock)
    rl.check("a")
    rl.check("a")
    assert not rl.check("a")[0]
    clock.t += 10.01
    assert rl.check("a")[0]


def test_keys_are_independent():
    rl = RateLimiter(1, 10, FakeClock())
    assert rl.check("a")[0]
    assert rl.check("b")[0]
    assert not rl.check("a")[0]


def test_invalid_config():
    with pytest.raises(ValueError):
        RateLimiter(0, 10)


def make_client(limit=2):
    clock = FakeClock()
    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(rate_limit(limit, 60, clock))])
    async def ping():
        return {"ok": True}

    return TestClient(app), clock


def test_endpoint_returns_429_with_headers():
    client, clock = make_client(2)
    r1 = client.get("/ping")
    assert r1.status_code == 200
    assert r1.headers["X-RateLimit-Remaining"] == "1"
    assert client.get("/ping").status_code == 200

    r3 = client.get("/ping")
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers

    clock.t += 61
    assert client.get("/ping").status_code == 200