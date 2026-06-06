import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

from flask import Blueprint, redirect, render_template, request, session, url_for

from storage import memory

authorize_bp = Blueprint("authorize", __name__)


@authorize_bp.route("/authorize", methods=["GET"])
def authorize():
    """v01: authorization code flow with client registry validation — no state, no PKCE."""
    if not session.get("logged_in"):
        session["authorize_params"] = request.args.to_dict()
        return redirect(url_for("login.login"))

    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    response_type = request.args.get("response_type")

    if not client_id or not redirect_uri or response_type != "code":
        return render_template(
            "error.html",
            status=400,
            message="Invalid authorization request",
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
        "code_challenge": None,
        "user_id": session.get("username"),
        "expires_at": datetime.now() + timedelta(seconds=3600),
        "used": False,
    }

    return redirect(f"{redirect_uri}?{urlencode({'code': code})}")
