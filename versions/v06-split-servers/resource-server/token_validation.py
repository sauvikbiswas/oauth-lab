"""Token validation helpers.

Read TOKEN_VALIDATION from env:
  - introspection: POST {AUTH_SERVER_URL}/introspect with INTROSPECTION_CLIENT_ID/SECRET
  - jwt: verify HS256 locally with JWT_SECRET

Return user_id (sub) on success, or None when invalid/expired.
Profile fields (username, email) are NOT in the token — look up
storage.profiles in routes/resource.py after validation.
"""

import os
import jwt
import requests
from typing import Any


def validate_bearer_token(token: str) -> dict[str, Any] | None:
    from routes.debug import record_validation

    mode = os.environ.get("TOKEN_VALIDATION", "introspection")
    result: dict[str, Any] | None = None
    error: str | None = None

    if mode == "introspection":
        result, error = _validate_via_introspection(token)
    elif mode == "jwt":
        result, error = _validate_via_jwt(token)
    else:
        error = f"Unknown TOKEN_VALIDATION={mode!r}; use introspection or jwt"
        record_validation(mode, None, error)
        raise ValueError(error)

    record_validation(mode, result, error)
    return result


def _validate_via_introspection(token: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.post(
            f"{os.environ.get('AUTH_SERVER_URL', 'http://localhost:25000')}/introspect",
            data={
                "token": token,
                "client_id": os.environ.get("INTROSPECTION_CLIENT_ID"),
                "client_secret": os.environ.get("INTROSPECTION_CLIENT_SECRET"),
            },
        )
    except requests.RequestException as exc:
        return None, f"introspect request failed: {exc}"

    if response.status_code != 200:
        return None, f"introspect HTTP {response.status_code}"

    body = response.json()
    if not body.get("active"):
        return None, "introspect returned active: false"

    sub = body.get("sub")
    if not sub:
        return None, "introspect missing sub"

    return {"user_id": sub}, None


def _validate_via_jwt(token: str) -> tuple[dict[str, Any] | None, str | None]:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        return None, "JWT_SECRET not set"

    try:
        decoded = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="resource-server",
            issuer="auth-server",
        )
    except jwt.InvalidTokenError:
        return None, "invalid or expired JWT"

    sub = decoded.get("sub")
    if not sub:
        return None, "JWT missing sub"

    return {"user_id": sub}, None
