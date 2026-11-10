import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.offline_capability import issue, validate
from main import app


def test_offline_capability_is_scoped_and_signed():
    token = issue("farmer-123", "Farmer@example.com", now=1000)
    payload = validate(token, now=1001)

    assert payload["scope"] == "offline_farmer"
    assert payload["user_id"] == "farmer-123"
    assert payload["email"] == "farmer@example.com"


def test_offline_capability_rejects_tampering_and_expiration():
    token = issue("farmer-123", "farmer@example.com", now=1000)
    payload, signature = token.split(".", 1)

    assert validate(f"{payload}x.{signature}", now=1001) is None
    assert validate(token, now=1000 + 30 * 24 * 60 * 60) is None


def test_offline_capability_cannot_submit_online_mutations():
    app.config["TESTING"] = False
    try:
        with app.test_client() as client:
            token = issue("farmer-123", "farmer@example.com")
            client.set_cookie("cocoscan_offline_capability", token)
            response = client.post("/farmer/submit-report", data={})
    finally:
        app.config["TESTING"] = True

    assert response.status_code == 403
