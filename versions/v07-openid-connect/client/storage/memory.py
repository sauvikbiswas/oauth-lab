"""In-memory storage stubs for the OAuth client.

Use these dicts while learning. Data is lost on restart.
Session holds the active oauth_state; memory mirrors flow history for /debug/state.
"""

# state -> {created_at}
pending_oauth_states: dict = {}

# authorization code -> {state, received_at}
authorization_codes: dict = {}

# access_token -> {expires_at, ...}  (v05+)
access_tokens: dict = {}
