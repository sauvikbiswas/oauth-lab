"""Protected resource API — GET /api/me.

"""

from flask import Blueprint, jsonify, request

from shared.resource_indicators import resource_a_indicator, resource_b_indicator
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

@resource_bp.route("/api/resource-a", methods=["GET"])
def resource_a():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({
            "error": "unauthorized",
            "error_description": "Bearer token is required",
        }), 401
    token = auth_header.split(" ", 1)[1]
    identity = validate_bearer_token(token, expected_resource=resource_a_indicator())
    if not identity:
        return jsonify({ 
            "error": "unauthorized",
            "error_description": "Invalid or expired token",
        }), 401
    return jsonify({
        "resource": "resource-a metadata",
    })

@resource_bp.route("/api/resource-b", methods=["GET"])
def resource_b():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({
            "error": "unauthorized",
            "error_description": "Bearer token is required",
        }), 401
    token = auth_header.split(" ", 1)[1]
    identity = validate_bearer_token(token, expected_resource=resource_b_indicator())
    if not identity:
        return jsonify({ 
            "error": "unauthorized",
            "error_description": "Invalid or expired token",
        }), 401
    return jsonify({
        "resource": "resource-b metadata",
    })