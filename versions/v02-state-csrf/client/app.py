import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os
import secrets
from datetime import datetime
from urllib.parse import urlencode

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
        return {"lab_version": "v02", "lab_role": "client"}

    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET"])
    def login():
        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state
        memory.pending_oauth_states[state] = {"created_at": datetime.now()}

        auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:5000").rstrip("/")
        params = {
            "response_type": "code",
            "client_id": os.environ.get("CLIENT_ID", "demo-client"),
            "redirect_uri": os.environ.get("REDIRECT_URI", "http://localhost:5001/callback"),
            "state": state,
        }
        return redirect(f"{auth_server}/authorize?{urlencode(params)}")

    @app.route("/callback", methods=["GET"])
    def callback():
        state = request.args.get("state")
        code = request.args.get("code")
        expected = session.pop("oauth_state", None)

        if not state:
            return render_template("callback.html", error="State is missing"), 400
        if not expected or state != expected:
            return render_template("callback.html", error="State mismatch"), 400
        if not code:
            return render_template("callback.html", error="Authorization code is missing"), 400

        memory.authorization_codes[code] = {
            "state": state,
            "received_at": datetime.now(),
        }
        return render_template("callback.html", code=code, state=state)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("CLIENT_APP_PORT", 5001))
    app.run(host="127.0.0.1", port=port, debug=True)
