"""Agent (middle service) — v10 token exchange (RFC 8693).

POST /exchange — proxy token exchange to the auth server.
GET /demo — standalone OBO matrix (subject vs exchanged token).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from jinja2 import ChoiceLoader, FileSystemLoader
from datetime import datetime

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters
from shared.resource_indicators import resource_a_indicator, resource_b_indicator, resource_server_base
from shared.token_exchange import GRANT_TYPE_TOKEN_EXCHANGE, TOKEN_TYPE_ACCESS_TOKEN

from routes.debug import debug_bp
from storage import memory

load_dotenv(Path(__file__).resolve().parent / ".env")


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


def _fetch_resource_api(access_token: str, path: str):
    resource_server = resource_server_base()
    return requests.get(
        f"{resource_server}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )


def _exchange_with_auth_server(subject_token: str, resource: str) -> tuple[dict, int]:
    auth_server = os.environ.get("AUTH_SERVER_URL", "http://localhost:25000").rstrip("/")
    try:
        resp = requests.post(
            f"{auth_server}/token",
            data={
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "client_id": os.environ.get("AGENT_CLIENT_ID", "demo-agent"),
                "client_secret": os.environ.get("AGENT_CLIENT_SECRET", "agent-secret"),
                "subject_token": subject_token,
                "subject_token_type": TOKEN_TYPE_ACCESS_TOKEN,
                "resource": resource,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        return {
            "error": "server_error",
            "error_description": f"Auth server unreachable: {exc}",
        }, 502
    try:
        payload = resp.json()
    except requests.JSONDecodeError:
        return {
            "error": "server_error",
            "error_description": f"Auth server returned non-JSON (status {resp.status_code})",
        }, 502
    if resp.status_code == 200 and payload.get("access_token"):
        memory.exchanged_tokens["last"] = {
            "access_token": payload["access_token"],
            "resource": resource,
            "expires_in": payload.get("expires_in"),
            "issued_token_type": payload.get("issued_token_type"),
            "exchanged_at": datetime.now(),
        }
    return payload, resp.status_code


def create_app() -> Flask:
    local_templates = Path(__file__).parent / "templates"
    app = Flask(__name__, static_folder=str(SHARED_STATIC))
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(local_templates)),
            FileSystemLoader(str(SHARED_TEMPLATES)),
        ]
    )
    register_lab_filters(app)

    @app.context_processor
    def inject_lab_context():
        return {"lab_version": "v10", "lab_role": "agent"}

    app.register_blueprint(debug_bp)

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            resource_a=resource_a_indicator(),
            resource_b=resource_b_indicator(),
        )

    @app.route("/exchange", methods=["POST"])
    def exchange():
        subject_token = request.form.get("subject_token")
        resource = request.form.get("resource")
        if not subject_token:
            return jsonify({"error": "invalid_request", "error_description": "subject_token is required"}), 400
        if not resource:
            return jsonify({"error": "invalid_request", "error_description": "resource is required"}), 400
        payload, status = _exchange_with_auth_server(subject_token, resource)
        return jsonify(payload), status

    @app.route("/demo", methods=["GET", "POST"])
    def demo():
        exchange_error = None
        exchanged_token = None
        subject_a = subject_b = exchanged_a = exchanged_b = None
        subject_token = request.form.get("subject_token", "").strip() if request.method == "POST" else ""

        if request.method == "POST":
            if not subject_token:
                exchange_error = "subject_token is required"
            else:
                payload, status = _exchange_with_auth_server(subject_token, resource_b_indicator())
                if status != 200 or payload.get("error"):
                    desc = payload.get("error_description", payload.get("error", "Token exchange failed"))
                    exchange_error = desc
                else:
                    exchanged_token = payload["access_token"]
                    subject_a = _resource_api_result(_fetch_resource_api(subject_token, "/api/resource-a"))
                    subject_b = _resource_api_result(_fetch_resource_api(subject_token, "/api/resource-b"))
                    exchanged_a = _resource_api_result(_fetch_resource_api(exchanged_token, "/api/resource-a"))
                    exchanged_b = _resource_api_result(_fetch_resource_api(exchanged_token, "/api/resource-b"))

        return render_template(
            "demo.html",
            subject_token=subject_token or None,
            exchange_error=exchange_error,
            exchanged_token=exchanged_token,
            subject_a=subject_a,
            subject_b=subject_b,
            exchanged_a=exchanged_a,
            exchanged_b=exchanged_b,
            resource_a_indicator=resource_a_indicator(),
            resource_b_indicator=resource_b_indicator(),
            client_debug_url=os.environ.get("CLIENT_APP_URL", "http://localhost:25001").rstrip("/") + "/debug/state?format=json",
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("AGENT_SERVER_PORT", 25003))
    app.run(host="localhost", port=port, debug=True)
