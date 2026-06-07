# OAuth 2 Learning Lab

Learn OAuth 2 by building it in versioned snapshots. Start with the simplest flow and add security one step at a time.

## Start here

**[v01 — Login and authorization code](versions/v01-login-and-code/README.md)**

Minimal runnable server + client: login, issue a `code`, redirect to callback. No `state`, no PKCE, no token endpoint.

See also: [docs/tutorial-overview.md](docs/tutorial-overview.md)

## Version roadmap

| Version | Status | Adds |
|---------|--------|------|
| [v01](versions/v01-login-and-code/) | **available** | login + code redirect; param resume; client registry + redirect_uri validation |
| [v02](versions/v02-state-csrf/) | **available** | OAuth `state` (CSRF); client generates + verifies, server requires + pass-through |

## Personal sandbox

[`versions/sandbox/`](versions/sandbox/) is an advanced work-in-progress, separate from the frozen tutorial snapshots. Use [v01](versions/v01-login-and-code/) for the guided path.

## Quick start (v01)

```bash
# Terminal 1
cd versions/v01-login-and-code/server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 2
cd versions/v01-login-and-code/client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

Open [http://localhost:5001](http://localhost:5001) and click **Start authorization**.

Log in as `user0` / `password0`. Expected callback:

```
http://localhost:5001/callback?code=<random-string>
```

## Learning resources

- [RFC 6749 — OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 — PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [OAuth 2.0 Simplified](https://www.oauth.com/)
