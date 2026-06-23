"""Protected resource API — GET /api/me."""

from flask import Blueprint, jsonify, request

from storage import profiles
from token_validation import validate_bearer_token

resource_bp = Blueprint("resource", __name__)


@resource_bp.route("/api/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({
            "error": "unauthorized",
            "error_description": "Bearer token is required",
        }), 401

    token = auth_header.split(" ", 1)[1]

    identity = validate_bearer_token(token)
    if not identity:
        return jsonify({
            "error": "unauthorized",
            "error_description": "Invalid or expired token",
        }), 401
    profile = profiles.profiles.get(identity.get("user_id"))
    if not profile:
        return jsonify({
            "error": "unauthorized",
            "error_description": "User not found",
        }), 401
    return jsonify({
        "user_id": identity.get("user_id"),
        "username": profile.get("username"),
        "email": profile.get("email"),
        "metadata": profile.get("metadata"),
    })
