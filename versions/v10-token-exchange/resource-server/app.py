import sys
from pathlib import Path

# Repo root on path so `shared` imports work when running from resource-server/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os

from dotenv import load_dotenv
from flask import Flask, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters

from routes.debug import debug_bp
from routes.resource import resource_bp

load_dotenv(Path(__file__).resolve().parent / ".env")


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
        return {"lab_version": "v10", "lab_role": "resource-server"}

    app.register_blueprint(resource_bp)
    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        validation = os.environ.get("TOKEN_VALIDATION", "introspection")
        return render_template("index.html", token_validation=validation)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("RESOURCE_SERVER_PORT", 25002))
    app.run(host="localhost", port=port, debug=True)
