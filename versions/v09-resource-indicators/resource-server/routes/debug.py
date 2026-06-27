from flask import Blueprint, jsonify, render_template, request

from storage import profiles

debug_bp = Blueprint("debug", __name__)

_last_validation: dict = {"mode": None, "result": None, "error": None}


@debug_bp.route("/debug/state", methods=["GET"])
def dump_state():
    """Dev-only: profile store and last token validation attempt."""
    payload = {
        "request_args": request.args.to_dict(),
        "last_validation": _last_validation,
        "storage": {
            "profiles": profiles.profiles,
        },
        "env": {
            "TOKEN_VALIDATION": __import__("os").environ.get("TOKEN_VALIDATION", "introspection"),
            "AUTH_SERVER_URL": __import__("os").environ.get("AUTH_SERVER_URL", "http://localhost:25000"),
        },
    }

    wants_html = (
        request.args.get("format") != "json"
        and request.accept_mimetypes.best_match(["application/json", "text/html"])
        == "text/html"
    )
    if wants_html:
        return render_template("debug_state.html", payload=payload)
    return jsonify(payload)


def record_validation(mode: str, result: dict | None, error: str | None = None) -> None:
    """Record the latest token validation attempt for /debug/state."""
    global _last_validation
    _last_validation = {"mode": mode, "result": result, "error": error}
