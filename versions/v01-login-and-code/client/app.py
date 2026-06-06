import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request
from jinja2 import ChoiceLoader, FileSystemLoader

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES

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

    @app.context_processor
    def inject_lab_context():
        return {"lab_version": "v01", "lab_role": "client"}

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/callback", methods=["GET"])
    def callback():
        return render_template("callback.html", code=request.args.get("code"))

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("CLIENT_APP_PORT", 5001))
    app.run(host="127.0.0.1", port=port, debug=True)
