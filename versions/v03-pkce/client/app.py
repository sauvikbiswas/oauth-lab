import sys
from pathlib import Path
import base64
import hashlib
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os
import secrets
from datetime import datetime
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session
from jinja2 import ChoiceLoader, FileSystemLoader

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters

from routes.debug import debug_bp
from storage import memory

load_dotenv()


def create_app() -> Flask:
    local_templates = Path(__file__).parent / "templates"
    app = Flask(__name__, static_folder=str(SHARED_STATIC))
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(local_templates)),
            FileSystemLoader(str(SHARED_TEMPLATES)),
        ]
    )
    register_lab_filters(app)

    @app.context_processor
    def inject_lab_context():
        return {"lab_version": "v03", "lab_role": "client"}

    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET"])
    def login():
        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state
        
        code_verifier = secrets.token_urlsafe(32)
        memory.pending_oauth_states[state] = {"created_at": datetime.now(), "code_verifier": code_verifier}
        session["code_verifier"] = code_verifier
        
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")

        auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:25000").rstrip("/")
        params = {
            "response_type": "code",
            "client_id": os.environ.get("CLIENT_ID", "demo-client"),
            "redirect_uri": os.environ.get("REDIRECT_URI", "http://localhost:25001/callback"),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return redirect(f"{auth_server}/authorize?{urlencode(params)}")

    @app.route("/callback", methods=["GET"])
    def callback():
        state = request.args.get("state")
        code = request.args.get("code")
        expected = session.pop("oauth_state", None)
        code_verifier = session.pop("code_verifier", None)

        if not state:
            return render_template("callback.html", error="State is missing"), 400
        if not expected or state != expected:
            return render_template("callback.html", error="State mismatch"), 400
        if not code:
            return render_template("callback.html", error="Authorization code is missing"), 400
        if not code_verifier:
            return render_template("callback.html", error="Code verifier is missing from session"), 400

        auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:25000").rstrip("/")
        resp = requests.post(
            f"{auth_server}/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": os.environ.get("REDIRECT_URI", "http://localhost:25001/callback"),
                "client_id": os.environ.get("CLIENT_ID", "demo-client"),
                "client_secret": os.environ.get("CLIENT_SECRET", "demo-secret"),
                "code_verifier": code_verifier,
            },
            timeout=10,
        )

        try:
            payload = resp.json()
        except requests.JSONDecodeError:
            hint = ""
            if resp.status_code == 403 and "localhost" in auth_server:
                hint = (
                    " Check AUTH_SERVER_URL in client/.env "
                    "(use http://localhost:25000 for the auth server)."
                )
            return render_template(
                "callback.html",
                error=f"Token endpoint returned non-JSON (status {resp.status_code}).{hint}",
            ), 502

        if resp.status_code != 200 or "error" in payload:
            desc = payload.get("error_description", payload.get("error", "Token exchange failed"))
            return render_template("callback.html", error=desc), resp.status_code

        access_token = payload["access_token"]
        memory.access_tokens[access_token] = {
            "state": state,
            "received_at": datetime.now(),
        }
        memory.authorization_codes[code] = {
            "state": state,
            "received_at": datetime.now(),
        }
        return render_template("callback.html", code=code, state=state, access_token=access_token)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("CLIENT_APP_PORT", 25001))
    app.run(host="localhost", port=port, debug=True)
