# v01 — Login and authorization code

The dumbest OAuth flow that works: user logs in, server issues a one-time `code`, browser lands on the client callback.

## You will learn

- Authorization server login
- `GET /authorize` issuing an authorization code
- Redirect back to the client with `?code=...`

## What's in v01

- Minimal session stash: `authorize_params` saved before login redirect, restored after successful login (so the flow works end-to-end)
- Pre-seeded `clients` registry; `client_id` and `redirect_uri` validated on `/authorize`
- Full in-memory storage shape (`authorization_codes`, `access_tokens`, `users`, `clients`) visible at `/debug/state`
- Redirect back to the client with `?code=...` (**no OAuth `state`**)
- Shared styled error page for login and authorize failures ([`shared/templates/error.html`](../../../shared/templates/error.html))

## What's intentionally missing (v02+)

- No OAuth `state` parameter (CSRF protection — v02)
- No PKCE (v03)
- No dedicated `/400` / `/401` error routes (v04)
- No `/token`, no `/api/me` (v05–v06)
- No full programmatic client wiring (v07)

## Styling

Pages use shared CSS from [`shared/static/lab.css`](../../../shared/static/lab.css) via [`shared/templates/base.html`](../../../shared/templates/base.html). Each app's `app.py` adds the repo root to `sys.path` so `shared` imports work — no `PYTHONPATH` needed.

## Run it

**Terminal 1 — server:**

```bash
cd versions/v01-login-and-code/server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

**Terminal 2 — client:**

```bash
cd versions/v01-login-and-code/client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

## Try it

1. Open [http://localhost:5001](http://localhost:5001) and click **Start authorization**, or open:

```
http://localhost:5000/authorize?response_type=code&client_id=demo-client&redirect_uri=http://localhost:5001/callback
```

2. Log in as `user0` / `password0`.

3. Browser should land on:

```
http://localhost:5001/callback?code=<random-string>
```

Note: **no `state`** in the callback URL — that is intentional for v01.

4. Inspect what was stored at [http://localhost:5000/debug/state](http://localhost:5000/debug/state) — session, `authorization_codes`, `clients`, and empty `access_tokens`. The browser shows a formatted HTML view; use `curl -H 'Accept: application/json' http://localhost:5000/debug/state` for raw JSON.

## What's next (v02)

Client generates `state`, server pass-through, client verifies on callback.
