"""Token validation helpers.

Read TOKEN_VALIDATION from env:
  - introspection: POST {AUTH_SERVER_URL}/introspect with INTROSPECTION_CLIENT_ID/SECRET
  - jwt: verify RS256 locally via JWKS from auth server (v08; was HS256 + JWT_SECRET in v07)

Return user_id (sub) on success, or None when invalid/expired.
Profile fields (username, email) are NOT in the token — look up
storage.profiles in routes/resource.py after validation.
"""

import os
import jwt
import requests
from typing import Any
import base64
from cryptography.hazmat.primitives.asymmetric import rsa

def _base64url_to_int(value: str) -> int:
    padding = "=" * (-len(value) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(value + padding), "big")


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
                "client_id": os.environ.get("INTROSPECTION_CLIENT_ID", "resource-server"),
                "client_secret": os.environ.get("INTROSPECTION_CLIENT_SECRET", "resource-secret"),
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
    resp = requests.get(f"{os.environ.get('AUTH_SERVER_URL', 'http://localhost:25000')}/jwks", timeout=10)
    if resp.status_code != 200:
        return None, f"jwks request failed: {resp.status_code}"
    try:
        jwks = resp.json()
    except requests.JSONDecodeError:
        return None, "Failed to parse JWKS response"

    try:
        access_token_header = jwt.get_unverified_header(token)
        kid = access_token_header.get("kid")
        if not kid:
            return None, "Access token header missing kid"
        jwk = next((key for key in jwks["keys"] if key["kid"] == kid), None)
        if not jwk:
            return None, "Public key not found"
        n = _base64url_to_int(jwk["n"])
        e = _base64url_to_int(jwk["e"])
        verify_key = rsa.RSAPublicNumbers(e, n).public_key()
        decoded = jwt.decode(
            token,
            verify_key,
            algorithms=["RS256"],
            audience="resource-server",
            issuer="auth-server",
        )
    except jwt.InvalidTokenError:
        return None, "invalid or expired JWT"

    sub = decoded.get("sub")
    if not sub:
        return None, "JWT missing sub"

    return {"user_id": sub}, None
