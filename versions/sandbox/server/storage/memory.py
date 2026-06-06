"""In-memory storage stubs for the authorization server.

Use these dicts while learning. Data is lost on restart.
Replace with sqlite.py when you want persistence.
"""

# authorization_code -> {client_id, redirect_uri, code_challenge, user_id, expires_at, used}
authorization_codes: dict = {}

# access_token -> {user_id, client_id, expires_at}
access_tokens: dict = {}

# username -> {password, user_id}  (learning only — do not store plaintext passwords in production)
users: dict = {
    "user0": {"password": "password0", "user_id": "user0"},
    "user1": {"password": "password1", "user_id": "user1"},
}

# client_id -> {client_secret, redirect_uris}
clients: dict = {
    "lab-client": {
        "client_secret": "lab-secret",
        "redirect_uris": ["http://localhost:5001/callback"],
    },
}