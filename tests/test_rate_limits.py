import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main


@pytest.fixture
def client():
    previous_testing = main.app.config.get("TESTING")
    previous_rate_limits = main.app.config.get("TEST_RATE_LIMITS")
    main.app.config["TESTING"] = True
    main.app.config["TEST_RATE_LIMITS"] = True
    with main.app.test_client() as test_client:
        yield test_client
    main.app.config["TESTING"] = previous_testing
    if previous_rate_limits is None:
        main.app.config.pop("TEST_RATE_LIMITS", None)
    else:
        main.app.config["TEST_RATE_LIMITS"] = previous_rate_limits


def test_login_rate_limit_returns_retry_after(client, monkeypatch):
    calls = {"count": 0}

    def limited(bucket, limit, window_seconds):
        calls["count"] += 1
        return False, 42

    monkeypatch.setattr(main.security_service, "check_request_rate_limit", limited)
    response = client.post("/login", data={"email": "a@example.com", "password": "bad"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "42"
    assert calls["count"] == 1


def test_get_login_is_not_rate_limited(client, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("GET login should not consume a rate-limit request")

    monkeypatch.setattr(main.security_service, "check_request_rate_limit", fail_if_called)
    assert client.get("/login").status_code == 200
