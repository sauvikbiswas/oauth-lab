"""Flask session helpers for OAuth state and PKCE verifier.

The client stores ephemeral OAuth data in a signed session cookie — not a database.
"""

from flask import session


def save_oauth_state(state: str, code_verifier: str) -> None:
    """Persist state and PKCE code_verifier before redirecting to the auth server.

    TODO: implement
        session["oauth_state"] = state
        session["code_verifier"] = code_verifier
    """
    raise NotImplementedError("TODO: save state and code_verifier to Flask session")


def pop_and_verify_state(incoming_state: str) -> str:
    """Verify callback state matches session and return the code_verifier.

    TODO: implement
        1. Read session["oauth_state"] and session["code_verifier"].
        2. Compare incoming_state to stored state (constant-time compare is ideal).
        3. Clear both keys from session.
        4. Return code_verifier for the token exchange.
        5. Raise or return error if state is missing or mismatched.

    Returns:
        The code_verifier string for POST /token.
    """
    raise NotImplementedError("TODO: verify state and return code_verifier from session")
