from flask import Blueprint, session, redirect, url_for, request
from storage import memory
from datetime import datetime, timedelta
import secrets
from urllib.parse import urlencode

authorize_bp = Blueprint("authorize", __name__)


@authorize_bp.route("/authorize", methods=["GET"])
def authorize():
    """Start the authorization code flow.

    Expected query parameters (you validate these):
        client_id               (required)
        redirect_uri            (required)
        response_type           (required, must be "code")
        state                   (required, pass back to client unchanged)
        code_challenge          (required for PKCE)
        code_challenge_method   (required, typically "S256")

    Note: 
    1. response_type is always "code" for this lab.
    2. code_challenge_method is always "S256" for this lab.
    3. optional parameter `scope` is not implemented.
    """

    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    state = request.args.get("state")
    code_challenge = request.args.get("code_challenge")
    code_challenge_method = request.args.get("code_challenge_method")

    # If required parameters are missing, return 400 error
    missing = [
        name for name in ["client_id", "redirect_uri", "response_type", "state", "code_challenge", "code_challenge_method"] if request.args.get(name) is None
    ]

    if missing:
        return redirect(url_for("error.error400", message=f"Missing required parameters: {', '.join(missing)}"))

    # If response type is not "code", return 400 error
    if request.args.get("response_type") != "code":
        return redirect(url_for("error.error400", message="Response type must be 'code'"))

    # If code challenge method is not "S256", return 400 error
    if request.args.get("code_challenge_method") != "S256":
        return redirect(url_for("error.error400", message="Code challenge method must be 'S256'"))

    # If user is not logged in, save the authorize parameters and redirect to login
    if not session.get("logged_in"):
        session["authorize_params"] = request.args.to_dict()
        return redirect(url_for("login.login"))
    else:

        # If client is not registered, or redirect URI is not registered, return 400 error
        registered_client = memory.clients.get(client_id)
        if not registered_client:
            return redirect(url_for("error.error400", message="Client not found"))

        if redirect_uri not in registered_client["redirect_uris"]:
            return redirect(url_for("error.error400", message="Redirect URI not found"))

        # Generate a one-time authorization code and store it in memory
        code = secrets.token_urlsafe(32)
        memory.authorization_codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "user_id": session.get("username"),
            "expires_at": datetime.now() + timedelta(seconds=3600)

        }

        # Redirect to the client's redirect URI with the authorization code and state
        return redirect(f"{redirect_uri}?{urlencode({'code': code, 'state': state})}")
