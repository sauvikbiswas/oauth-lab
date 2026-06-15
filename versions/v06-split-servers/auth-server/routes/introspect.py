"""RFC 7662 token introspection.

The resource server authenticates as a service client (see memory.service_clients),
not as demo-client. Returns identity only (sub); profile lives on the resource server.
"""

import os
from datetime import datetime

import jwt
from flask import Blueprint, jsonify, request

from storage import memory

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
    }


def _active_from_jwt(token: str) -> dict | None:
    """Stateless JWT access tokens: verify signature and claims locally."""
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        return None
    try:
        decoded = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="resource-server",
            issuer="auth-server",
        )
    except jwt.InvalidTokenError:
        return None
    sub = decoded.get("sub")
    if not sub:
        return None
    return {
        "active": True,
        "sub": sub,
        "client_id": decoded.get("client_id"),
        "exp": decoded.get("exp", 0),
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
