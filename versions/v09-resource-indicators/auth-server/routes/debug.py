import json
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session

from shared.resource_indicators import allowed_resources
from storage import memory

debug_bp = Blueprint("debug", __name__)


def _serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


@debug_bp.route("/debug/state", methods=["GET"])
def dump_state():
    """Dev-only: dump Flask session, request args, and in-memory storage."""
    payload = {
        "request_args": request.args.to_dict(),
        "session": dict(session),
        "storage": {
            "authorization_codes": memory.authorization_codes,
            "access_tokens": memory.access_tokens,
            "refresh_tokens": memory.refresh_tokens,
            "users": memory.users,
            "clients": memory.clients,
            "service_clients": memory.service_clients,
            "allowed_resources": sorted(allowed_resources()),
        },
    }
    payload = json.loads(json.dumps(payload, default=_serialize))

    wants_html = (
        request.args.get("format") != "json"
        and request.accept_mimetypes.best_match(["application/json", "text/html"])
        == "text/html"
    )
    if wants_html:
        return render_template("debug_state.html", payload=payload)
    return jsonify(payload)
