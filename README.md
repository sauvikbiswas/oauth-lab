# OAuth 2 Learning Lab

Learn OAuth 2 by building it in versioned snapshots. Start with the simplest flow and add security one step at a time.

Auth server: `:25000` · Client: `:25001` (see [`.env.example`](.env.example)).

## Start here

**[v01 — Login and authorization code](versions/v01-login-and-code/)**

Minimal runnable server + client: login, issue a `code`, redirect to callback. No `state`, no PKCE, no token endpoint.

Latest available snapshot: **[v03 — PKCE](versions/v03-pkce/)** (authorization code + PKCE + `POST /token`).

## Version roadmap

| Version | Status | Adds |
|---------|--------|------|
| [v01](versions/v01-login-and-code/) | **available** | login + code redirect; param resume; client registry + `redirect_uri` validation |
| [v02](versions/v02-state-csrf/) | **available** | OAuth `state` (CSRF); client generates + verifies, server requires + pass-through |
| [v03](versions/v03-pkce/) | **available** | PKCE (`code_challenge` / `code_verifier`); `POST /token`; client code exchange |

Diff adjacent versions to see exactly what changed:

```bash
diff -ru versions/v02-state-csrf versions/v03-pkce
```

## Personal sandbox

[`versions/sandbox/`](versions/sandbox/) is an advanced work-in-progress, separate from the frozen tutorial snapshots. Use [v01](versions/v01-login-and-code/) for the guided path.

## Quick start (v01)

```bash
# Terminal 1 — authorization server
cd versions/v01-login-and-code/server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 2 — client
cd versions/v01-login-and-code/client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

Open [http://localhost:25001](http://localhost:25001) and click **Start authorization**.

Log in as `user0` / `password0`. Expected callback:

```
http://localhost:25001/callback?code=<random-string>
```

For v03, use `versions/v03-pkce/` instead (same two-terminal pattern). Callback should show `code`, `state`, and `access_token`.

## Learning resources

- [RFC 6749 — OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 — PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [OAuth 2.0 Simplified](https://www.oauth.com/)
