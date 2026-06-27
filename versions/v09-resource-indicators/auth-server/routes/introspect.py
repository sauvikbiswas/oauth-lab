"""RFC 7662 token introspection — v09 scaffold on v08.

TODO(v09 Step 8): include `aud` (resource indicator) in active introspection responses.
TODO(v09 Step 8): reject tokens whose bound resource does not match the caller's expected API.
"""

from datetime import datetime

import jwt
from flask import Blueprint, jsonify, request

from shared.resource_indicators import allowed_resources
from storage import memory
from keys import get_private_key

introspect_bp = Blueprint("introspect", __name__)


def _authenticate_service_client() -> tuple[bool, str | None]:
    client_id = request.form.get("client_id")
    client_secret = request.form.get("client_secret")
    if not client_id or not client_secret:
        return False, None
    registered = memory.service_clients.get(client_id)
    if not registered or registered["client_secret"] != client_secret:
        return False, None
    return True, client_id


def _active_from_memory(token: str) -> dict | None:
    """Opaque tokens: lookup server-side store (supports revocation by deletion)."""
    token_data = memory.access_tokens.get(token)
    if not token_data:
        return None
    if token_data["expires_at"] < datetime.now():
        return None
    return {
        "active": True,
        "sub": token_data["user_id"],
        "client_id": token_data["client_id"],
        "exp": int(token_data["expires_at"].timestamp()),
        "aud": token_data["resource"],
    }


def _active_from_jwt(token: str) -> dict | None:
    """Stateless JWT access tokens: verify signature and claims locally."""
    private_key = get_private_key()
    public_key = private_key.public_key()
    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer="auth-server",
            options={"verify_aud": False},
        )
    except jwt.InvalidTokenError:
        return None
    sub = decoded.get("sub")
    if not sub:
        return None
    aud = decoded.get("aud")
    if not aud or aud not in allowed_resources():
        return None
    scope_raw = decoded.get("scope", "")
    scope = scope_raw.split() if isinstance(scope_raw, str) else []
    return {
        "active": True,
        "sub": sub,
        "client_id": decoded.get("client_id"),
        "scope": scope,
        "exp": decoded.get("exp", 0),
        "aud": aud,
    }


@introspect_bp.route("/introspect", methods=["POST"])
def introspect():
    ok, _caller_id = _authenticate_service_client()
    if not ok:
        return jsonify({
            "error": "invalid_client",
            "error_description": "Service client authentication failed",
        }), 401

    token = request.form.get("token")
    if not token:
        return jsonify({"active": False})

    payload = _active_from_memory(token)
    if payload is None:
        payload = _active_from_jwt(token)
    if payload is None:
        return jsonify({"active": False})

    return jsonify(payload)
