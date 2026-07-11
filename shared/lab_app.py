"""Flask app bootstrap shared from v11 onward.

Every lab app repeats the same setup in its `create_app()`: create a Flask
app served from `shared/static`, layer local `templates/` over
`shared/templates`, set the secret key and a per-app session cookie name,
register the JSON highlight filter, and inject `lab_version`/`lab_role`
into the template context. This factory captures that boilerplate so v11+
apps can call `create_lab_app(...)` instead of copying ~20 lines into each
`app.py`.

Earlier snapshots (v01-v10) keep their inline `create_app()` on purpose,
so `diff -ru` between adjacent versions stays readable. Route registration,
index views, and app-specific config stay in each app's own `app.py`.
"""

import os
from pathlib import Path

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from shared.paths import SHARED_STATIC, SHARED_TEMPLATES
from shared.jinja_filters import register_lab_filters


def create_lab_app(
    import_name: str,
    app_dir: str | Path,
    *,
    lab_version: str,
    lab_role: str,
    session_cookie_name: str,
) -> Flask:
    """Build a Flask app with the lab's shared static/template/filter wiring.

    Args:
        import_name: value to pass as Flask's import name (usually ``__name__``).
        app_dir: the app directory that holds a local ``templates/`` folder
            (usually ``Path(__file__).parent``).
        lab_version: e.g. ``"v11"``; exposed to templates as ``lab_version``.
        lab_role: e.g. ``"client"`` / ``"auth-server"``; exposed as ``lab_role``.
        session_cookie_name: distinct per app so multiple apps can run on
            localhost without clobbering each other's session cookie.

    The caller still registers blueprints and routes on the returned app.
    """
    local_templates = Path(app_dir) / "templates"
    app = Flask(import_name, static_folder=str(SHARED_STATIC))
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(local_templates)),
            FileSystemLoader(str(SHARED_TEMPLATES)),
        ]
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SESSION_COOKIE_NAME"] = session_cookie_name
    register_lab_filters(app)

    @app.context_processor
    def inject_lab_context():
        return {"lab_version": lab_version, "lab_role": lab_role}

    return app
