"""In-memory storage for the agent (middle service).
"""

# subject_token fingerprint or exchange id -> {access_token, resource, expires_at, act?}
exchanged_tokens: dict = {}
