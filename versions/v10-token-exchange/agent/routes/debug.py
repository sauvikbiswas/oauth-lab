import json
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from storage import memory

debug_bp = Blueprint("debug", __name__)


def _serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


@debug_bp.route("/debug/state", methods=["GET"])
def dump_state():
    payload = {
        "request_args": request.args.to_dict(),
        "storage": {
            "exchanged_tokens": memory.exchanged_tokens,
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
