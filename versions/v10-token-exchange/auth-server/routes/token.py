"""Token endpoint — v10 on v09.

v09: authorization_code + refresh_token with RFC 8707 `resource`.
v10: RFC 8693 token-exchange grant on POST /token (agent-authenticated, A→B policy).
"""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt
import os

from keys import get_private_key
from flask import Blueprint, jsonify, request

from shared.token_exchange import GRANT_TYPE_TOKEN_EXCHANGE, TOKEN_TYPE_ACCESS_TOKEN
from shared.resource_indicators import allowed_resources, resource_a_indicator, resource_b_indicator
from storage import memory
from routes.introspect import _authenticate_agent_client, _active_from_memory, _active_from_jwt

token_bp = Blueprint("token", __name__)

ACCESS_TOKEN_TTL = 60
REFRESH_TOKEN_TTL = 3600


def _invalid_grant(description: str):
    return jsonify({"error": "invalid_grant", "error_description": description}), 400


def _invalid_client(description: str):
    return jsonify({"error": "invalid_client", "error_description": description}), 401


def _oidc_issuer() -> str:
    return os.environ.get("OIDC_ISSUER", os.environ.get("AUTH_SERVER_URL", "http://localhost:25000")).rstrip("/")


def _mint_id_token(user_id: str, client_id: str, nonce: str, scope: list[str]) -> str:
    private_key = get_private_key()

    expires_at = datetime.now() + timedelta(seconds=ACCESS_TOKEN_TTL)
    id_token_claims = {
        "iss": _oidc_issuer(),
        "sub": user_id,
        "aud": client_id,
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now().timestamp()),
        "nonce": nonce,
    }
    # add email/name claims when scope includes email/profile
    if "email" in scope:
        id_token_claims["email"] = memory.users[user_id]["email"]
    if "profile" in scope:
        id_token_claims["name"] = memory.users[user_id]["name"]

    return jwt.encode(id_token_claims, private_key, algorithm="RS256", headers={"kid": "oauth-lab-v101"})


def _token_response(access_token: str, refresh_token: str, expires_in: int, id_token: str | None = None):
    body = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
    }
    # include id_token in body when openid was in the authorization code scope
    if id_token is not None:
        body["id_token"] = id_token
    return jsonify(body)


def _token_exchange_response(access_token: str, expires_in: int):
    return jsonify({
        "access_token": access_token,
        "issued_token_type": TOKEN_TYPE_ACCESS_TOKEN,
        "token_type": "Bearer",
        "expires_in": expires_in,
    })


def _mint_access_token(
    user_id: str,
    client_id: str,
    scope: list[str] | None = None,
    resource: str | None = None,
    act: dict | None = None,
) -> tuple[str, int]:
    expires_at = datetime.now() + timedelta(seconds=ACCESS_TOKEN_TTL)
    scope = scope or []

    if os.environ.get("ACCESS_TOKEN_FORMAT", "opaque") == "jwt":
        private_key = get_private_key()
        payload = {
            "iss": "auth-server",
            "aud": resource,
            "iat": int(datetime.now().timestamp()),
            "sub": user_id,
            "client_id": client_id,
            "scope": " ".join(scope),
            "exp": int(expires_at.timestamp()),
        }
        if act is not None:
            payload["act"] = act
        access_token = jwt.encode(
            payload,
            private_key,
            algorithm="RS256",
            headers={"kid": "oauth-lab-v101"},
        )
    else:
        access_token = secrets.token_urlsafe(32)
        memory.access_tokens[access_token] = {
            "user_id": user_id,
            "client_id": client_id,
            "expires_at": expires_at,
            "scope": scope,
            "resource": resource,
        }
        if act is not None:
            memory.access_tokens[access_token]["act"] = act

    return access_token, ACCESS_TOKEN_TTL


def _mint_token_pair(user_id: str, client_id: str, scope: list[str] | None = None, resource: str | None = None) -> tuple[str, str, int]:
    access_token, expires_in = _mint_access_token(user_id, client_id, scope, resource)

    refresh_token = secrets.token_urlsafe(32)
    memory.refresh_tokens[refresh_token] = {
        "user_id": user_id,
        "client_id": client_id,
        "scope": scope or [],
        "expires_at": datetime.now() + timedelta(seconds=REFRESH_TOKEN_TTL),
        "resource": resource,
    }

    return access_token, refresh_token, expires_in


def _handle_authorization_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    code_verifier: str,
    resource: str | None = None,
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

    if authorization_code["resource"] != resource:
        return _invalid_grant("Resource mismatch")

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    if authorization_code["code_challenge"] != code_challenge:
        return _invalid_grant("PKCE verification failed")

    memory.authorization_codes[code]["used"] = True
    memory.authorization_codes[code]["resource"] = resource

    scope = authorization_code.get("scope") or []

    access_token, refresh_token, expires_in = _mint_token_pair(
        authorization_code["user_id"],
        authorization_code["client_id"],
        scope,
        resource,
    )

    id_token = None
    if "openid" in scope:
        id_token = _mint_id_token(
            authorization_code["user_id"],
            authorization_code["client_id"],
            authorization_code["nonce"],
            scope,
        )

    return _token_response(access_token, refresh_token, expires_in, id_token)


def _handle_refresh_token(refresh_token_value: str, client_id: str, resource: str | None = None):
    if not refresh_token_value:
        return _invalid_grant("Refresh token is required")

    refresh_token_data = memory.refresh_tokens.get(refresh_token_value)
    if not refresh_token_data:
        return _invalid_grant("Refresh token not found")

    if refresh_token_data["client_id"] != client_id:
        return _invalid_grant("Client ID mismatch")

    if refresh_token_data["expires_at"] < datetime.now():
        return _invalid_grant("Refresh token expired")

    if refresh_token_data["resource"] != resource:
        return _invalid_grant("Resource mismatch")

    access_token, expires_in = _mint_access_token(
        refresh_token_data["user_id"],
        refresh_token_data["client_id"],
        refresh_token_data.get("scope") or [],
        refresh_token_data.get("resource"),
    )
    return _token_response(access_token, refresh_token_value, expires_in)


def _handle_token_exchange(client_id: str):
    ok, _ = _authenticate_agent_client()
    if not ok:
        return _invalid_client("Agent client authentication failed")
    
    subject_token = request.form.get("subject_token")
    if not subject_token:
        return _invalid_grant("Subject token is required")

    subject_token_type = request.form.get("subject_token_type")
    if not subject_token_type:
        return _invalid_grant("Subject token type is required")
    
    if subject_token_type != TOKEN_TYPE_ACCESS_TOKEN:
        return _invalid_grant("Subject token type must be access_token")

    payload = _active_from_memory(subject_token)
    if payload is None:
        payload = _active_from_jwt(subject_token)
    if payload is None:
        return _invalid_grant("Subject token is invalid")

    resource = request.form.get("resource") or request.form.get("audience")
    if not resource:
        return _invalid_grant("Resource or audience is required")
    
    resource_allowlist = allowed_resources()
    if resource not in resource_allowlist:
        return _invalid_grant("Resource not allowed")

    if payload["aud"] != resource_a_indicator():
        return _invalid_grant("Subject token must be bound to Resource A")

    if resource != resource_b_indicator():
        return _invalid_grant("Exchange only allowed for Resource B")

    access_token, expires_in = _mint_access_token(
        payload["sub"],
        client_id,
        resource=resource,
        act={"sub": client_id}
    )
    return _token_exchange_response(access_token, expires_in)


@token_bp.route("/token", methods=["POST"])
def token():
    grant_type = request.form.get("grant_type")
    client_id = request.form.get("client_id")
    client_secret = request.form.get("client_secret")

    if not client_id:
        return _invalid_grant("Client ID is required")

    if not client_secret:
        return _invalid_grant("Client secret is required")

    if grant_type == GRANT_TYPE_TOKEN_EXCHANGE:
        return _handle_token_exchange(client_id)

    if grant_type == "authorization_code":
        return _handle_authorization_code(
            code=request.form.get("code"),
            redirect_uri=request.form.get("redirect_uri"),
            client_id=client_id,
            code_verifier=request.form.get("code_verifier"),
            resource=request.form.get("resource"),
        )

    if grant_type == "refresh_token":
        return _handle_refresh_token(
            refresh_token_value=request.form.get("refresh_token"),
            client_id=client_id,
            resource=request.form.get("resource"),
        )

    return _invalid_grant("Grant type must be 'authorization_code', 'refresh_token', or token-exchange")
