from flask import Blueprint, redirect, render_template, request, session, url_for

from storage import memory

login_bp = Blueprint("login", __name__)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        return render_template("login.html", error="Username and password are required"), 401

    user = memory.users.get(username)
    if user and user["password"] == password:
        session["logged_in"] = True
        session["username"] = username
        params = session.pop("authorize_params", {})
        if params:
            return redirect(url_for("authorize.authorize", **params))
        return redirect(url_for("welcome"))
    return render_template("login.html", error="Invalid username or password"), 401
