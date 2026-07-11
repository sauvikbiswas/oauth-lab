"""PKCE (RFC 7636) helpers, shared from v11 onward.

Mirrors the inline S256 logic that the client and the auth server's token
route recopy in every snapshot from v03 through v10 (see, e.g.,
`client/app.py` `_start_authorize` and `auth-server/routes/token.py`
`_verify_pkce`). Extracted so future snapshots can import these helpers
instead of duplicating the same handful of lines.

Earlier snapshots (v01-v10) keep PKCE inline on purpose, so `diff -ru`
between adjacent versions still shows the mechanics being introduced.
"""

import base64
import hashlib
import secrets


def generate_code_verifier(nbytes: int = 32) -> str:
    """Return a high-entropy, URL-safe PKCE code verifier."""
    return secrets.token_urlsafe(nbytes)


def code_challenge_s256(code_verifier: str) -> str:
    """Return the S256 code challenge for a verifier (base64url, no padding)."""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def verify_code_verifier(code_verifier: str, expected_challenge: str) -> bool:
    """True when the verifier hashes (S256) to the stored challenge."""
    if not code_verifier:
        return False
    return code_challenge_s256(code_verifier) == expected_challenge
