from flask import Blueprint, redirect, render_template_string, request, session, url_for

from storage import memory

login_bp = Blueprint("login", __name__)

LOGIN_FORM = """
<!DOCTYPE html>
<html>
<head><title>[sandbox] Login</title><link rel="stylesheet" href="/static/lab.css"></head>
<body class="lab-server">
  <h1>Authorization Server — Login</h1>
  <form method="post">
    <label>Username <input name="username" /></label><br/>
    <label>Password <input name="password" type="password" /></label><br/>
    <button type="submit">Log in</button>
  </form>
  <p><em>TODO: wire up authentication and redirect back to /authorize.</em></p>
</body>
</html>
"""


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate the resource owner before issuing an authorization code.

    Flow you implement:
        1. GET: show login form (template above is a starting point).
        2. POST: validate credentials against storage/memory.py users dict.
        3. On success, mark user as logged in (session) and resume /authorize.
        4. On failure, re-render form with an error message.
    """
    if request.method == "GET":
        return render_template_string(LOGIN_FORM)

    username = request.form["username"]
    password = request.form["password"]
    user = memory.users.get(username)
    if user and user["password"] == password:
        session["logged_in"] = True
        session["username"] = username
        params = session.pop("authorize_params", {})
        return redirect(url_for("authorize.authorize", **params))
    else:
        return redirect(url_for("error.error401", message="Invalid username or password"))
