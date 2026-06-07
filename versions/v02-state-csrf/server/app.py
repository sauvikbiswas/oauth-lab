import sys
from pathlib import Path

# Repo root on path so `shared` imports work when running from server/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from jinja2 import ChoiceLoader, FileSystemLoader

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters

from routes.authorize import authorize_bp
from routes.debug import debug_bp
from routes.login import login_bp

load_dotenv()


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
        return {"lab_version": "v02", "lab_role": "server"}

    app.register_blueprint(authorize_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/welcome")
    def welcome():
        if not session.get("logged_in"):
            return redirect(url_for("login.login"))
        return render_template(
            "welcome.html",
            username=session.get("username"),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("AUTH_SERVER_PORT", 25000))
    app.run(host="localhost", port=port, debug=True)
