import sys
from pathlib import Path

# Repo root on path so `shared` imports work when running from server/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os

from dotenv import load_dotenv
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters

from routes.authorize import authorize_bp
from routes.debug import debug_bp
from routes.login import login_bp
from routes.resource import resource_bp
from routes.token import token_bp
from routes.error import error_bp

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
        return {"lab_version": "sandbox", "lab_role": "server"}

    app.register_blueprint(authorize_bp)
    app.register_blueprint(token_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(debug_bp)
    app.register_blueprint(error_bp)

    @app.route("/")
    def index():
        return (
            "<!DOCTYPE html><html><head><title>[sandbox] Authorization Server</title>"
            "<link rel='stylesheet' href='/static/lab.css'></head><body class='lab-server'>"
            "<h1>OAuth Authorization Server</h1>"
            "<p>Endpoints: "
            "<a href='/authorize'>/authorize</a>, "
            "<a href='/token'>/token</a> (POST), "
            "<a href='/login'>/login</a>, "
            "<a href='/api/me'>/api/me</a>, "
            "<a href='/debug/state'>/debug/state</a>"
            "</p>"
            "<p><em>Protocol logic not implemented — see README checklist.</em></p>"
            "</body></html>"
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("AUTH_SERVER_PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
