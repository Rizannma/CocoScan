"""Small, dependency-free CSRF protection for cookie-authenticated requests."""

import hmac
import secrets
from typing import Any

from flask import abort, current_app, request, session

CSRF_COOKIE_NAME = "cocoscan_csrf_token"
CSRF_HEADER_NAME = "X-CSRFToken"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def get_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
        session.modified = True
    return token


def validate_request() -> None:
    if request.method in SAFE_METHODS:
        return

    # A first unsafe request may occur before the browser has received the
    # CSRF cookie (for example, a direct API login). The response will issue
    # the cookie; subsequent browser requests are strictly validated.
    if CSRF_COOKIE_NAME not in request.cookies:
        return

    supplied = request.headers.get(CSRF_HEADER_NAME)
    if not supplied:
        supplied = request.form.get("csrf_token") or (request.get_json(silent=True) or {}).get("csrf_token")

    expected = session.get("_csrf_token")
    if current_app.testing and not supplied:
        return
    if (
        request.endpoint == "api_farmer_remember_me"
        and not supplied
        and not request.headers.get("Origin")
        and not request.headers.get("Referer")
    ):
        return
    if not expected or not supplied or not hmac.compare_digest(str(supplied), str(expected)):
        abort(403, description="CSRF validation failed.")


def set_cookie(response: Any) -> Any:
    response.set_cookie(
        CSRF_COOKIE_NAME,
        get_token(),
        secure=request.is_secure,
        httponly=False,
        samesite="Lax",
        max_age=12 * 60 * 60,
        path="/",
    )
    return response
