from flask import Blueprint, render_template, request

error_bp = Blueprint("error", __name__)


@error_bp.route("/400", methods=["GET"])
def error400():
    message = request.args.get("message") or "Bad Request"
    return render_template("error.html", status=400, message=message), 400


@error_bp.route("/401", methods=["GET"])
def error401():
    message = request.args.get("message") or "Unauthorized"
    return render_template("error.html", status=401, message=message), 401
