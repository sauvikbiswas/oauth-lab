from flask import Blueprint, request

resource_bp = Blueprint("resource", __name__)


@resource_bp.route("/api/me", methods=["GET"])
def me():
    """Protected resource — returns info about the authenticated user.

    Expected header:
        Authorization: Bearer <access_token>

    Flow you implement:
        1. Parse Bearer token from Authorization header.
        2. Look up token in storage/memory.py access_tokens dict.
        3. Reject with 401 if missing, unknown, or expired.
        4. Return JSON user profile, e.g. {"user_id": "...", "username": "..."}.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return (
            {"error": "unauthorized", "error_description": "TODO: implement Bearer token validation"},
            401,
        )

    # TODO: validate token and return user profile
    return (
        {"error": "not_implemented", "error_description": "TODO: implement GET /api/me"},
        501,
    )
