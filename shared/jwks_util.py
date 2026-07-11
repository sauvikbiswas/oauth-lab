"""JWKS / RSA verification helpers, shared from v11 onward.

Mirrors the inline JWK -> RSA public key logic duplicated in both the
client (`client/app.py`) and the resource server
(`resource-server/token_validation.py`) from v08 onward, where each fetches
`/jwks`, finds the key by `kid`, and rebuilds an RSA public key from the
`n`/`e` parameters before verifying an RS256 token. Extracted so future
snapshots can import these helpers instead of recopying them.

Earlier snapshots (v08-v10) keep this logic inline on purpose, so `diff -ru`
between adjacent versions still shows the verification being introduced.
"""

import base64

import requests
from cryptography.hazmat.primitives.asymmetric import rsa


def base64url_to_int(value: str) -> int:
    """Decode a base64url JWK parameter (e.g. ``n`` or ``e``) to an int."""
    padding = "=" * (-len(value) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(value + padding), "big")


def jwk_to_rsa_public_key(jwk: dict):
    """Rebuild an RSA public key object from an RSA JWK's ``n`` and ``e``."""
    n = base64url_to_int(jwk["n"])
    e = base64url_to_int(jwk["e"])
    return rsa.RSAPublicNumbers(e, n).public_key()


def fetch_jwks(auth_server_url: str, timeout: float = 10) -> dict:
    """GET the auth server's ``/jwks`` document and return the parsed JSON."""
    resp = requests.get(f"{auth_server_url.rstrip('/')}/jwks", timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def find_jwk_for_kid(jwks: dict, kid: str) -> dict | None:
    """Return the JWK in ``jwks['keys']`` matching ``kid``, or None."""
    return next((key for key in jwks.get("keys", []) if key.get("kid") == kid), None)
