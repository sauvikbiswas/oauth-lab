import base64
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt
import os

from flask import Blueprint, jsonify, request

from storage import memory

token_bp = Blueprint("token", __name__)

ACCESS_TOKEN_TTL = 60
REFRESH_TOKEN_TTL = 3600


def _invalid_grant(description: str):
    return jsonify({"error": "invalid_grant", "error_description": description}), 400


def _token_response(access_token: str, refresh_token: str, expires_in: int):
    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
    })


def _mint_access_token(user_id: str, client_id: str) -> tuple[str, int]:
    expires_at = datetime.now() + timedelta(seconds=ACCESS_TOKEN_TTL)

    if os.environ.get("ACCESS_TOKEN_FORMAT", "opaque") == "jwt":
        access_token = jwt.encode(
            {
                "iss": "auth-server",
                "aud": "resource-server",
                "iat": int(datetime.now().timestamp()),
                "sub": user_id,
                "client_id": client_id,
                "exp": int(expires_at.timestamp()),
            },
            os.getenv("JWT_SECRET"),
            algorithm="HS256",
        )
    else:
        access_token = secrets.token_urlsafe(32)
        memory.access_tokens[access_token] = {
            "user_id": user_id,
            "client_id": client_id,
            "expires_at": expires_at,
        }

    return access_token, ACCESS_TOKEN_TTL


def _mint_token_pair(user_id: str, client_id: str) -> tuple[str, str, int]:
    access_token, expires_in = _mint_access_token(user_id, client_id)

    refresh_token = secrets.token_urlsafe(32)
    memory.refresh_tokens[refresh_token] = {
        "user_id": user_id,
        "client_id": client_id,
        "expires_at": datetime.now() + timedelta(seconds=REFRESH_TOKEN_TTL),
    }

    return access_token, refresh_token, expires_in


def _handle_authorization_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    code_verifier: str,
):
    if not code:
        return _invalid_grant("Code is required")

    if not redirect_uri:
        return _invalid_grant("Redirect URI is required")

    if not code_verifier:
        return jsonify({"error": "invalid_request", "error_description": "Code verifier is required"}), 400

    authorization_code = memory.authorization_codes.get(code)
    if not authorization_code:
        return _invalid_grant("Authorization code not found")

    if authorization_code["redirect_uri"] != redirect_uri:
        return _invalid_grant("Redirect URI mismatch")

    if authorization_code["client_id"] != client_id:
        return _invalid_grant("Client ID mismatch")

    if authorization_code["expires_at"] < datetime.now():
        return _invalid_grant("Authorization code expired")

    if authorization_code["used"]:
        return _invalid_grant("Authorization code already used")

    if authorization_code["code_challenge_method"] != "S256":
        return _invalid_grant("Code challenge method not supported")

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    if authorization_code["code_challenge"] != code_challenge:
        return _invalid_grant("PKCE verification failed")

    memory.authorization_codes[code]["used"] = True

    access_token, refresh_token, expires_in = _mint_token_pair(
        authorization_code["user_id"],
        authorization_code["client_id"],
    )
    return _token_response(access_token, refresh_token, expires_in)


def _handle_refresh_token(refresh_token_value: str, client_id: str):
    if not refresh_token_value:
        return _invalid_grant("Refresh token is required")

    refresh_token_data = memory.refresh_tokens.get(refresh_token_value)
    if not refresh_token_data:
        return _invalid_grant("Refresh token not found")

    if refresh_token_data["client_id"] != client_id:
        return _invalid_grant("Client ID mismatch")

    if refresh_token_data["expires_at"] < datetime.now():
        return _invalid_grant("Refresh token expired")

    access_token, expires_in = _mint_access_token(
        refresh_token_data["user_id"],
        refresh_token_data["client_id"],
    )
    return _token_response(access_token, refresh_token_value, expires_in)


@token_bp.route("/token", methods=["POST"])
def token():
    grant_type = request.form.get("grant_type")
    client_id = request.form.get("client_id")
    client_secret = request.form.get("client_secret")

    if not client_id:
        return _invalid_grant("Client ID is required")

    if not client_secret:
        return _invalid_grant("Client secret is required")

    if grant_type == "authorization_code":
        return _handle_authorization_code(
            code=request.form.get("code"),
            redirect_uri=request.form.get("redirect_uri"),
            client_id=client_id,
            code_verifier=request.form.get("code_verifier"),
        )

    if grant_type == "refresh_token":
        return _handle_refresh_token(
            refresh_token_value=request.form.get("refresh_token"),
            client_id=client_id,
        )

    return _invalid_grant("Grant type must be 'authorization_code' or 'refresh_token'")
