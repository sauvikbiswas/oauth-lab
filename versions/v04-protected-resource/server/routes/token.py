from datetime import datetime, timedelta
import secrets
from storage import memory
from flask import Blueprint, request, jsonify
import base64
import hashlib
token_bp = Blueprint("token", __name__)


@token_bp.route("/token", methods=["POST"])
def token():
    grant_type = request.form.get("grant_type")
    code = request.form.get("code")
    redirect_uri = request.form.get("redirect_uri")
    client_id = request.form.get("client_id")
    client_secret = request.form.get("client_secret")
    code_verifier = request.form.get("code_verifier")

    if grant_type != "authorization_code":
        return jsonify({"error": "invalid_grant", "error_description": "Grant type must be 'authorization_code'"}), 400

    if not code:
        return jsonify({"error": "invalid_grant", "error_description": "Code is required"}), 400

    if not redirect_uri:
        return jsonify({"error": "invalid_grant", "error_description": "Redirect URI is required"}), 400

    if not client_id:
        return jsonify({"error": "invalid_grant", "error_description": "Client ID is required"}), 400

    if not client_secret:
        return jsonify({"error": "invalid_grant", "error_description": "Client secret is required"}), 400

    if not code_verifier:
        return jsonify({"error": "invalid_request", "error_description": "Code verifier is required"}), 400

    authorization_code = memory.authorization_codes.get(code)
    if not authorization_code:
        return jsonify({"error": "invalid_grant", "error_description": "Authorization code not found"}), 400

    if authorization_code["redirect_uri"] != redirect_uri:
        return jsonify({"error": "invalid_grant", "error_description": "Redirect URI mismatch"}), 400

    if authorization_code["client_id"] != client_id:
        return jsonify({"error": "invalid_grant", "error_description": "Client ID mismatch"}), 400

    if authorization_code["expires_at"] < datetime.now():
        return jsonify({"error": "invalid_grant", "error_description": "Authorization code expired"}), 400

    if authorization_code["used"]:
        return jsonify({"error": "invalid_grant", "error_description": "Authorization code already used"}), 400

    if authorization_code["code_challenge_method"] != "S256":
        return jsonify({"error": "invalid_grant", "error_description": "Code challenge method not supported"}), 400
    
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
    if authorization_code["code_challenge"] != code_challenge:
        return jsonify({"error": "invalid_grant", "error_description": "PKCE verification failed"}), 400

    memory.authorization_codes[code]["used"] = True

    access_token = secrets.token_urlsafe(32)
    memory.access_tokens[access_token] = {
        "user_id": authorization_code["user_id"],
        "client_id": authorization_code["client_id"],
        "expires_at": datetime.now() + timedelta(seconds=3600),
    }

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
    })