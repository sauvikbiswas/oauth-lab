"""RSA key pair and JWK helpers for v08+ — RS256 signing and JWKS publication."""

from cryptography.hazmat.primitives.asymmetric import rsa
from typing import Any

import base64

def _int_to_base64url(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(length, "big")).decode().rstrip("=")

_private_key = None

def get_private_key():
    global _private_key
    if _private_key is None:
        _private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
    return _private_key


def get_jwks() -> dict[str, Any]:
    private_key = get_private_key()
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    n = _int_to_base64url(public_numbers.n)
    e = _int_to_base64url(public_numbers.e)
    return {
        "keys": [
            {
                "kid": "oauth-lab-v091",
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "n": n,
                "e": e,
            }
        ]
    }
