import html
import json

from markupsafe import Markup


def _render_json(value, indent: int) -> str:
    space = "  " * indent
    inner = "  " * (indent + 1)

    if value is None:
        return '<span class="json-null">null</span>'
    if value is True:
        return '<span class="json-boolean">true</span>'
    if value is False:
        return '<span class="json-boolean">false</span>'
    if isinstance(value, (int, float)):
        return f'<span class="json-number">{value}</span>'
    if isinstance(value, str):
        return f'<span class="json-string">{html.escape(json.dumps(value))}</span>'

    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        items = list(value.items())
        for index, (key, item) in enumerate(items):
            comma = "," if index < len(items) - 1 else ""
            key_html = f'<span class="json-key">{html.escape(json.dumps(key))}</span>'
            lines.append(f"{inner}{key_html}: {_render_json(item, indent + 1)}{comma}")
        lines.append(f"{space}}}")
        return "\n".join(lines)

    if isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for index, item in enumerate(value):
            comma = "," if index < len(value) - 1 else ""
            lines.append(f"{inner}{_render_json(item, indent + 1)}{comma}")
        lines.append(f"{space}]")
        return "\n".join(lines)

    return html.escape(json.dumps(value))


def highlight_json(value) -> Markup:
    """Pretty-print JSON with span wrappers for syntax coloring."""
    return Markup(_render_json(value, 0))


def register_lab_filters(app) -> None:
    app.jinja_env.filters["highlight_json"] = highlight_json
