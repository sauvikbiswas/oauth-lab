"""Profile data owned by the resource server.

Keyed by user_id (same value as sub from introspection / JWT).
The auth server authenticates users; this API owns display profile fields.
"""

# user_id -> {username, email}
profiles: dict = {
    "user0": {"username": "User Number 0", "email": "user0@oauth-lab.me"},
    "user1": {"username": "User Number 1", "email": "user1@oauth-lab.me"},
}
