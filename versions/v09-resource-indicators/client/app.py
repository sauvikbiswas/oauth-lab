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
from cryptography.hazmat.primitives.asymmetric import rsa

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters
from shared.resource_indicators import resource_a_indicator, resource_b_indicator, resource_server_base

from routes.debug import debug_bp
from storage import memory

load_dotenv(Path(__file__).resolve().parent / ".env")


def _base64url_to_int(value: str) -> int:
    padding = "=" * (-len(value) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(value + padding), "big")


def _resource_indicator_for(target: str) -> str | None:
    if target == "resource-a":
        return resource_a_indicator()
    if target == "resource-b":
        return resource_b_indicator()
    return None


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
        return {"lab_version": "v09", "lab_role": "client"}

    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        access_token = session.get("access_token")
        profile = None
        if access_token:
            resource_server = resource_server_base()
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
        return render_template(
            "index.html",
            access_token=access_token,
            profile=profile,
            session_resource=session.get("resource_indicator"),
        )

    def _start_authorize(resource: str):
        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state
        session["resource_indicator"] = resource

        code_verifier = secrets.token_urlsafe(32)
        memory.pending_oauth_states[state] = {"created_at": datetime.now(), "code_verifier": code_verifier}
        session["code_verifier"] = code_verifier

        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip("=")

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
            "resource": resource,
        }
        return redirect(f"{auth_server}/authorize?{urlencode(params)}")

    @app.route("/login", methods=["GET"])
    @app.route("/login/<target>", methods=["GET"])
    def login(target: str | None = None):
        if target is None:
            return render_template(
                "login.html",
                resource_a_indicator=_resource_indicator_for("resource-a"),
                resource_b_indicator=_resource_indicator_for("resource-b"),
            )

        resource = _resource_indicator_for(target)
        if not resource:
            return render_template(
                "login.html",
                error=f"Unknown resource target: {target}",
                resource_a_indicator=_resource_indicator_for("resource-a"),
                resource_b_indicator=_resource_indicator_for("resource-b"),
            ), 400

        return _start_authorize(resource)

    @app.route("/logout", methods=["GET"])
    def logout():
        session.pop("access_token", None)
        session.pop("refresh_token", None)
        session.pop("token_grant", None)
        session.pop("id_token", None)
        session.pop("nonce", None)
        session.pop("resource_indicator", None)
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
                "resource": session.get("resource_indicator"),
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

    def fetch_resource_api(access_token: str, path: str):
        resource_server = resource_server_base()
        return requests.get(
            f"{resource_server}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

    def _resource_api_result(resp) -> dict:
        try:
            body = resp.json()
        except requests.JSONDecodeError:
            body = None
        return {
            "status": resp.status_code,
            "body": body,
            "ok": resp.status_code == 200,
        }

    def fetch_profile(access_token: str):
        resource_server = resource_server_base()
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
                "resource": session.get("resource_indicator"),
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

        resp = requests.get(f"{issuer}/jwks", timeout=10)
        if resp.status_code != 200:
            return render_template("profile.html", error=f"Failed to fetch JWKS (status {resp.status_code})"), resp.status_code
        try:
            jwks = resp.json()
        except requests.JSONDecodeError:
            return render_template("profile.html", error="Failed to parse JWKS response"), 502
        id_token_header = jwt.get_unverified_header(id_token)
        
        kid = id_token_header.get("kid")
        if not kid:
            return render_template("profile.html", error="ID token header missing kid"), 401
        jwk = next((key for key in jwks["keys"] if key["kid"] == kid), None)
        if not jwk:
            return render_template("profile.html", error="Public key not found"), 401

        n = _base64url_to_int(jwk["n"])
        e = _base64url_to_int(jwk["e"])
        verify_key = rsa.RSAPublicNumbers(e, n).public_key()

        try:
            id_token_claims = jwt.decode(
                id_token,
                verify_key,
                algorithms=["RS256"],
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

        resource_a = _resource_api_result(fetch_resource_api(access_token, "/api/resource-a"))
        resource_b = _resource_api_result(fetch_resource_api(access_token, "/api/resource-b"))

        return render_template(
            "profile.html",
            id_token_claims=id_token_claims,
            userinfo=userinfo,
            profile=profile_data,
            token_grant=session.get("token_grant"),
            resource_indicator=session.get("resource_indicator"),
            resource_a=resource_a,
            resource_b=resource_b,
            resource_a_indicator=_resource_indicator_for("resource-a"),
            resource_b_indicator=_resource_indicator_for("resource-b"),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("CLIENT_APP_PORT", 25001))
    app.run(host="localhost", port=port, debug=True)
