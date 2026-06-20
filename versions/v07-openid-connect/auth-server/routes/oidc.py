"""OIDC routes — v07 stubs. Implement per docs/learning-oauth-2-07.

Step 4: GET /.well-known/openid-configuration
Step 5: GET /userinfo
"""

import os

from flask import Blueprint, jsonify, request

from routes.introspect import _active_from_jwt, _active_from_memory
from storage import memory

oidc_bp = Blueprint("oidc", __name__)


@oidc_bp.route("/.well-known/openid-configuration", methods=["GET"])
def openid_configuration():
    issuer = os.environ.get(
        "OIDC_ISSUER",
        os.environ.get("AUTH_SERVER_URL", "http://localhost:25000"),
    ).rstrip("/")

    return jsonify({
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/authorize",
        "token_endpoint": f"{issuer}/token",
        "userinfo_endpoint": f"{issuer}/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "scopes_supported": ["openid", "email", "profile"],
        "code_challenge_methods_supported": ["S256"],
    })


def _bearer_access_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    return token or None


@oidc_bp.route("/userinfo", methods=["GET"])
def userinfo():
    token = _bearer_access_token()
    if not token:
        return jsonify({
            "error": "invalid_token",
            "error_description": "Bearer access token required",
        }), 401

    active = _active_from_memory(token)
    scope: list[str] = []
    if active:
        scope = memory.access_tokens.get(token, {}).get("scope") or []
    else:
        active = _active_from_jwt(token)
        if not active:
            return jsonify({
                "error": "invalid_token",
                "error_description": "Invalid or expired access token",
            }), 401

    user = memory.users.get(active["sub"])
    claims = {}
    if "openid" in scope:
        claims["sub"] = active["sub"]
    if "email" in scope and user:
        claims["email"] = user["email"]
    if "profile" in scope and user:
        claims["name"] = user["name"]

    return jsonify(claims)
