"""In-memory storage stubs for the authorization server.

Auth server holds authentication data only: credentials and stable subject ids.
Display profile (username, email) lives on the resource server — see
resource-server/storage/profiles.py.

Use these dicts while learning. Data is lost on restart.
"""

# authorization_code -> {client_id, redirect_uri, code_challenge, user_id, expires_at, used}
authorization_codes: dict = {}

# access_token -> {user_id, client_id, expires_at, scope}  (opaque Mode A only)
access_tokens: dict = {}

# refresh_token -> {user_id, client_id, scope, expires_at}
refresh_tokens: dict = {}

# login username -> {password, user_id, email, name}
# Learning only — do not store plaintext passwords in production.
users: dict = {
    "user0": {"password": "password0", "user_id": "user0", "email": "user0@oauth-lab.me", "name": "User Number 0"},
    "user1": {"password": "password1", "user_id": "user1", "email": "user1@oauth-lab.me", "name": "User Number 1"},
}

# OAuth web clients: Authorization Code flow (redirect URIs, user delegation).
# client_id -> {client_secret, redirect_uris}
clients: dict = {
    "demo-client": {
        "client_secret": "demo-secret",
        "redirect_uris": ["http://localhost:25001/callback"],
    },
}

# Backend service clients: call protected auth-server endpoints (e.g. POST /introspect).
# Not the same role as clients above — production often stores these in a separate table.
# client_id -> {client_secret}
service_clients: dict = {
    "resource-server": {
        "client_secret": "resource-secret",
    },
}