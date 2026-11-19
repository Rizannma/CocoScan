import os
import sys
import time

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
    assert "upgrade-insecure-requests" not in response.headers["Content-Security-Policy"]
    assert "cocoscan_csrf_token=" in response.headers.get("Set-Cookie", "")


def test_https_request_upgrades_insecure_requests(client):
    response = client.get("/login", base_url="https://localhost")

    assert "upgrade-insecure-requests" in response.headers["Content-Security-Policy"]


def test_login_form_submits_csrf_token(client):
    base_url = "https://localhost"
    response = client.get("/login", base_url=base_url)
    assert b'name="csrf_token"' in response.data

    csrf_cookie = next(
        header.split(";", 1)[0].split("=", 1)[1]
        for header in response.headers.getlist("Set-Cookie")
        if header.startswith("cocoscan_csrf_token=")
    )
    response = client.post(
        "/login",
        base_url=base_url,
        data={"csrf_token": csrf_cookie, "email": "", "password": ""},
    )

    assert response.status_code != 403


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


def test_session_keep_alive_refreshes_authenticated_non_farmer_session(client):
    previous_activity = time.time() - 300
    with client.session_transaction() as sess:
        sess["user_id"] = "00000000-0000-0000-0000-000000000099"
        sess["user_role"] = "admin"
        sess["last_active"] = previous_activity

    response = client.post("/session/keep-alive")

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    with client.session_transaction() as sess:
        assert sess["last_active"] > previous_activity


def test_session_keep_alive_rejects_farmer_session(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "00000000-0000-0000-0000-000000000001"
        sess["user_role"] = "farmer"
        sess["last_active"] = time.time()

    response = client.post("/session/keep-alive")

    assert response.status_code in {302, 403}


def test_inactivity_logout_displays_reason_on_login(client):
    response = client.get("/logout?reason=inactivity", follow_redirects=True)

    assert response.status_code == 200
    assert b"You were signed out after 15 minutes of inactivity." in response.data


def test_server_timeout_displays_warning_on_login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "00000000-0000-0000-0000-000000000098"
        sess["user_email"] = "admin@example.com"
        sess["user_role"] = "admin"
        sess["last_active"] = time.time() - 901

    response = client.get("/admin/storage-backups", follow_redirects=True)

    assert response.status_code == 200
    assert b"Your session has expired due to 15 minutes of inactivity." in response.data


def test_farmer_is_redirected_when_opening_admin_dashboard_directly(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "00000000-0000-0000-0000-000000000001"
        sess["user_role"] = "farmer"
        sess["user_email"] = "farmer@example.com"

    response = client.get("/admin/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/farmer/dashboard")
