"""OAuth client helpers — you implement the protocol steps here."""

import os


def build_auth_url(state: str, code_challenge: str) -> str:
    """Build the authorization server /authorize redirect URL.

    TODO: implement
        - Read AUTH_SERVER_URL, CLIENT_ID, REDIRECT_URI from environment.
        - Construct URL with query params:
            client_id, redirect_uri, response_type=code,
            scope, state, code_challenge, code_challenge_method=S256

    Returns:
        Full URL to redirect the user's browser to.
    """
    raise NotImplementedError("TODO: build authorization URL with PKCE params")


def exchange_code(code: str, code_verifier: str) -> dict:
    """Exchange authorization code for tokens via POST /token.

    TODO: implement
        - POST to {AUTH_SERVER_URL}/token with application/x-www-form-urlencoded body:
            grant_type=authorization_code, code, redirect_uri,
            client_id, client_secret, code_verifier
        - Parse JSON response; handle RFC 6749 error responses.
        - Return token payload, e.g. {"access_token": "...", "token_type": "Bearer", ...}

    Note: this runs server-side in the Flask client app — the browser never sees client_secret.
    """
    raise NotImplementedError("TODO: POST /token and return token response")


def get_profile(access_token: str) -> dict:
    """Call the protected resource with a Bearer token.

    TODO: implement
        - GET {AUTH_SERVER_URL}/api/me
        - Header: Authorization: Bearer {access_token}
        - Return parsed JSON user profile or raise on 401/5xx.
    """
    raise NotImplementedError("TODO: GET /api/me with Bearer token")
