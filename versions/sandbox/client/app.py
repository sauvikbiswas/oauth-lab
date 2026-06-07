import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request

from shared.paths import SHARED_STATIC

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(SHARED_STATIC))
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET"])
    def login():
        """Start OAuth flow: generate state + PKCE, save to session, redirect to auth server.

        TODO: implement
            1. Generate cryptographically random state and code_verifier.
            2. Derive code_challenge = BASE64URL(SHA256(code_verifier)).
            3. Call session.save_oauth_state(state, code_verifier).
            4. Redirect to oauth.client.build_auth_url(state, code_challenge).
        """
        return (
            "TODO: implement GET /login — generate state/PKCE and redirect to auth server",
            501,
        )

    @app.route("/callback", methods=["GET"])
    def callback():
        """Handle redirect from authorization server.

        Expected query params: code, state (and optionally error, error_description).

        TODO: implement
            1. If error param present, show error page.
            2. Call session.pop_and_verify_state(request.args["state"]).
            3. Call oauth.client.exchange_code(code, code_verifier).
            4. Store access_token in session; call get_profile; render callback.html.
        """
        return render_template(
            "callback.html",
            error="TODO: implement callback handler — see app.py docstring",
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("CLIENT_APP_PORT", 25001))
    app.run(host="localhost", port=port, debug=True)
