import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

from flask import Blueprint, redirect, render_template, request, session, url_for

from storage import memory

authorize_bp = Blueprint("authorize", __name__)


@authorize_bp.route("/authorize", methods=["GET"])
def authorize():
    """v02 scaffold: same as v01 with state CSRF implemented."""
    if not session.get("logged_in"):
        session["authorize_params"] = request.args.to_dict()
        return redirect(url_for("login.login"))

    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    response_type = request.args.get("response_type")
    state = request.args.get("state")
    code_challenge = request.args.get("code_challenge")
    code_challenge_method = request.args.get("code_challenge_method")
    # parse scope (space-separated); require nonce when openid in scope.
    scope = request.args.get("scope")
    nonce = request.args.get("nonce")

    if scope and "openid" in scope:
        if not nonce:
            return render_template(
                "error.html",
                status=400,
                message="Nonce is required when openid is in scope",
            ), 400

    scope = scope.split(" ") if scope else []

    if (
        not client_id
        or not redirect_uri
        or response_type != "code"
        or not state
        or not code_challenge
        or not code_challenge_method
    ):
        return render_template(
            "error.html",
            status=400,
            message="Invalid authorization request",
        ), 400

    if code_challenge_method != "S256":
        return render_template(
            "error.html",
            status=400,
            message="Code challenge method must be S256",
        ), 400

    registered_client = memory.clients.get(client_id)
    if not registered_client:
        return render_template("error.html", status=400, message="Client not found"), 400
    if redirect_uri not in registered_client["redirect_uris"]:
        return render_template("error.html", status=400, message="Redirect URI not found"), 400

    code = secrets.token_urlsafe(32)
    memory.authorization_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "user_id": session.get("username"),
        "expires_at": datetime.now() + timedelta(seconds=3600),
        "used": False,
        # persist validated scope and nonce
        "scope": scope,
        "nonce": nonce,
    }

    return redirect(f"{redirect_uri}?{urlencode({'code': code, 'state': state})}")
