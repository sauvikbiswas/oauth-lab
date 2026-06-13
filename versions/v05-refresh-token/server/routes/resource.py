from flask import Blueprint, jsonify, request
from storage import memory
from datetime import datetime

resource_bp = Blueprint("resource", __name__)


@resource_bp.route("/api/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify( { "error": "unauthorized", "error_description": "Bearer token is required", }), 401

    token = auth_header.split(" ")[1]
    token_data = memory.access_tokens.get(token)
    if not token_data:
        return jsonify({"error": "unauthorized", "error_description": "Token not found"}), 401

    if token_data["expires_at"] < datetime.now():
        return jsonify({"error": "unauthorized", "error_description": "Token expired"}), 401

    user_id = token_data["user_id"]
    user_data = memory.users.get(user_id)
    if not user_data:
        return jsonify({"error": "unauthorized", "error_description": "User not found"}), 401

    return jsonify({
        "user_id": user_id,
        "username": user_data["username"],
        "email": user_data["email"],
    }), 200