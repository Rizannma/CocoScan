import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main


@pytest.fixture
def client():
    main.app.config["TESTING"] = True
    with main.app.test_client() as test_client:
        yield test_client


def test_security_headers_are_present(client):
    response = client.get("/login")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "cocoscan_csrf_token=" in response.headers.get("Set-Cookie", "")


def test_state_changing_request_requires_csrf_after_cookie_issuance(client):
    main.app.config["TESTING"] = False
    client.get("/login")

    response = client.post("/login", data={"email": "", "password": ""})

    assert response.status_code == 403
    main.app.config["TESTING"] = True


def test_csrf_header_allows_state_changing_request(client):
    response = client.get("/login")
    csrf_cookie = next(
        header.split(";", 1)[0].split("=", 1)[1]
        for header in response.headers.getlist("Set-Cookie")
        if header.startswith("cocoscan_csrf_token=")
    )

    response = client.post(
        "/login",
        data={"email": "", "password": ""},
        headers={"X-CSRFToken": csrf_cookie},
    )

    assert response.status_code != 403
