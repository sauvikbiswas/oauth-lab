from flask import Blueprint, request

token_bp = Blueprint("token", __name__)


@token_bp.route("/token", methods=["POST"])
def token():
    """Exchange an authorization code for tokens.

    Expected body (application/x-www-form-urlencoded):
        grant_type      (required, must be "authorization_code")
        code            (required)
        redirect_uri    (required, must match authorize request)
        client_id       (required)
        client_secret   (required for confidential clients)
        code_verifier   (required for PKCE)

    Flow you implement:
        1. Validate grant_type and client credentials.
        2. Look up authorization code; reject if missing, expired, or already used.
        3. Verify redirect_uri and client_id match what was stored with the code.
        4. Verify PKCE: SHA256(code_verifier) base64url-encoded == stored code_challenge.
        5. Mark code as used; generate access_token (optional: refresh_token).
        6. Return JSON: {"access_token": "...", "token_type": "Bearer", "expires_in": 3600}

    Error responses should follow RFC 6749 format:
        {"error": "invalid_grant", "error_description": "..."}
    """
    # TODO: implement token endpoint
    return (
        {"error": "not_implemented", "error_description": "TODO: implement POST /token"},
        501,
    )
