import sys
from pathlib import Path

# Repo root on path so `shared` imports work when running from server/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from jinja2 import ChoiceLoader, FileSystemLoader

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters

from routes.authorize import authorize_bp
from routes.debug import debug_bp
from routes.login import login_bp

load_dotenv()


def _authorize_url() -> str:
    auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:5000").rstrip("/")
    return (
        f"{auth_server}/authorize?"
        f"{urlencode({'response_type': 'code', 'client_id': os.environ.get('CLIENT_ID', 'demo-client'), 'redirect_uri': os.environ.get('REDIRECT_URI', 'http://localhost:5001/callback')})}"
    )


def create_app() -> Flask:
    local_templates = Path(__file__).parent / "templates"
    app = Flask(__name__, static_folder=str(SHARED_STATIC))
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(local_templates)),
            FileSystemLoader(str(SHARED_TEMPLATES)),
        ]
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    register_lab_filters(app)

    @app.context_processor
    def inject_lab_context():
        return {"lab_version": "v01", "lab_role": "server"}

    app.register_blueprint(authorize_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        return render_template("index.html", authorize_url=_authorize_url())

    @app.route("/welcome")
    def welcome():
        if not session.get("logged_in"):
            return redirect(url_for("login.login"))
        return render_template(
            "welcome.html",
            username=session.get("username"),
            authorize_url=_authorize_url(),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("AUTH_SERVER_PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
