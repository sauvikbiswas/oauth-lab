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
from flask import Flask, redirect, render_template, request, session, url_for
from jinja2 import ChoiceLoader, FileSystemLoader
import jwt

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters

from routes.debug import debug_bp
from storage import memory

load_dotenv(Path(__file__).resolve().parent / ".env")

def create_app() -> Flask:
    local_templates = Path(__file__).parent / "templates"
    app = Flask(__name__, static_folder=str(SHARED_STATIC))
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SESSION_COOKIE_NAME"] = "oauth_client_session"
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(local_templates)),
            FileSystemLoader(str(SHARED_TEMPLATES)),
        ]
    )
    register_lab_filters(app)

    @app.context_processor
    def inject_lab_context():
        return {"lab_version": "v07", "lab_role": "client"}

    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        access_token = session.get("access_token")
        profile = None
        if access_token:
            # TODO(v06 Step 5): profile comes from resource server, not auth server.
            resource_server = os.environ.get("RESOURCE_SERVER_URL", "http://localhost:25002").rstrip("/")
            try:
                resp = requests.get(
                    f"{resource_server}/api/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10,
                )
                if resp.status_code == 200:
                    profile = resp.json()
            except requests.RequestException:
                pass
        return render_template("index.html", access_token=access_token, profile=profile)

    @app.route("/login", methods=["GET"])
    def login():
        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state
        
        code_verifier = secrets.token_urlsafe(32)
        memory.pending_oauth_states[state] = {"created_at": datetime.now(), "code_verifier": code_verifier}
        session["code_verifier"] = code_verifier
        
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")

        scope = os.environ.get("OIDC_SCOPES", "openid email profile").split(" ")
        nonce = secrets.token_urlsafe(32)
        session["nonce"] = nonce

        auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:25000").rstrip("/")
        params = {
            "response_type": "code",
            "client_id": os.environ.get("CLIENT_ID", "demo-client"),
            "redirect_uri": os.environ.get("REDIRECT_URI", "http://localhost:25001/callback"),
            "state": state,
            "nonce": nonce,
            "scope": " ".join(scope),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return redirect(f"{auth_server}/authorize?{urlencode(params)}")

    @app.route("/logout", methods=["GET"])
    def logout():
        session.pop("access_token", None)
        session.pop("refresh_token", None)
        session.pop("token_grant", None)
        session.pop("id_token", None)
        session.pop("nonce", None)
        return redirect("/")

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

        session["access_token"] = access_token
        session["refresh_token"] = payload["refresh_token"]
        session["token_grant"] = "authorization_code"
        if payload.get("id_token"):
            session["id_token"] = payload["id_token"]
        return redirect(url_for("profile"))

    def fetch_profile(access_token: str):
        # TODO(v06 Step 5): call resource server, not auth server.
        resource_server = os.environ.get("RESOURCE_SERVER_URL", "http://localhost:25002").rstrip("/")
        return requests.get(
            f"{resource_server}/api/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

    def fetch_userinfo(access_token: str):
        auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:25000").rstrip("/")
        return requests.get(
            f"{auth_server}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

    def refresh_access_token() -> bool:
        refresh_token = session.get("refresh_token")
        if not refresh_token:
            return False
        auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:25000").rstrip("/")
        resp = requests.post(
            f"{auth_server}/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": os.environ.get("CLIENT_ID", "demo-client"),
                "client_secret": os.environ.get("CLIENT_SECRET", "demo-secret"),
            },
            timeout=10,
        )
        try:
            payload = resp.json()
        except requests.JSONDecodeError:
            return False
        if resp.status_code != 200 or "error" in payload:
            session.pop("access_token", None)
            session.pop("refresh_token", None)
            session.pop("token_grant", None)
            return False
        session["access_token"] = payload["access_token"]
        if payload.get("refresh_token"):
            session["refresh_token"] = payload["refresh_token"]
        session["token_grant"] = "refresh_token"
        return True

    @app.route("/profile", methods=["GET"])
    def profile():
        id_token = session.get("id_token")
        if not id_token:
            return render_template("profile.html", error="ID token is missing from session. Are you logged in?"), 401

        issuer = os.environ.get(
            "OIDC_ISSUER",
            os.environ.get("AUTH_SERVER_URL", "http://localhost:25000"),
        ).rstrip("/")
        try:
            id_token_claims = jwt.decode(
                id_token,
                os.getenv("JWT_SECRET"),
                algorithms=["HS256"],
                audience=os.environ.get("CLIENT_ID", "demo-client"),
                issuer=issuer,
            )
        except jwt.InvalidTokenError:
            return render_template("profile.html", error="Invalid or expired ID token."), 401

        expected_nonce = session.get("nonce")
        if not expected_nonce or id_token_claims.get("nonce") != expected_nonce:
            return render_template("profile.html", error="ID token nonce mismatch."), 401

        access_token = session.get("access_token")
        if not access_token:
            if not refresh_access_token():
                return render_template(
                    "profile.html",
                    error="Access token is missing from session. Are you logged in?",
                ), 401
            access_token = session["access_token"]

        resp = fetch_profile(access_token)
        if resp.status_code == 401:
            if not refresh_access_token():
                return render_template("profile.html", error="Session expired. Please log in again."), 401
            access_token = session["access_token"]
            resp = fetch_profile(access_token)

        if resp.status_code != 200:
            return render_template("profile.html", error=f"Failed to fetch profile (status {resp.status_code})"), resp.status_code

        try:
            profile_data = resp.json()
        except requests.JSONDecodeError:
            return render_template("profile.html", error="Failed to parse profile response"), 502

        resp = fetch_userinfo(access_token)
        if resp.status_code == 401:
            if not refresh_access_token():
                return render_template("profile.html", error="Session expired. Please log in again."), 401
            access_token = session["access_token"]
            resp = fetch_userinfo(access_token)

        if resp.status_code != 200:
            return render_template("profile.html", error=f"Failed to fetch userinfo (status {resp.status_code})"), resp.status_code

        try:
            userinfo = resp.json()
        except requests.JSONDecodeError:
            return render_template("profile.html", error="Failed to parse userinfo response"), 502

        return render_template(
            "profile.html",
            id_token_claims=id_token_claims,
            userinfo=userinfo,
            profile=profile_data,
            token_grant=session.get("token_grant"),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("CLIENT_APP_PORT", 25001))
    app.run(host="localhost", port=port, debug=True)
