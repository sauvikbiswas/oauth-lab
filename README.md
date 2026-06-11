# OAuth 2 Learning Lab

Learn OAuth 2 by building it in versioned snapshots. Start with the simplest flow and add one security or protocol idea per version.

Auth server: `:25000` · Client: `:25001` (see [`.env.example`](.env.example)).

## Start here

**[v01 — Login and authorization code](versions/v01-login-and-code/)**

Minimal runnable server + client: login, issue a `code`, redirect to callback. No `state`, no PKCE, no token endpoint.

**Latest snapshot: [v04 — Protected resource](versions/v04-protected-resource/)**  
Authorization Code + PKCE, token exchange, Bearer `GET /api/me`, client profile page.

**Next (planned): [v05 — Refresh tokens](versions/v05-refresh-token/)**  
Short-lived access tokens; `grant_type=refresh_token`; silent client refresh.

Write-up for the full arc: [`docs/tutorial-overview.md`](docs/tutorial-overview.md).

## Version roadmap

| Version | Status | Adds |
|---------|--------|------|
| [v01](versions/v01-login-and-code/) | **available** | login + code redirect; param resume; client registry + `redirect_uri` validation |
| [v02](versions/v02-state-csrf/) | **available** | OAuth `state` (CSRF); client generates + verifies, server requires + pass-through |
| [v03](versions/v03-pkce/) | **available** | PKCE (`code_challenge` / `code_verifier`); `POST /token`; client code exchange |
| [v04](versions/v04-protected-resource/) | **available** | `GET /api/me` (Bearer); client session token; `/profile` and logout |
| [v05](versions/v05-refresh-token/) | **planned** | refresh tokens; silent client refresh — [implementation plan](versions/v05-refresh-token/README.md) |

Diff adjacent versions to see exactly what changed:

```bash
diff -ru versions/v03-pkce versions/v04-protected-resource
```

(v05 is plan-only until scaffolded from v04.)

## Personal sandbox

[`versions/sandbox/`](versions/sandbox/) is an advanced work-in-progress, separate from the frozen tutorial snapshots. Use [v01](versions/v01-login-and-code/) for the guided path.

## Quick start

Same two-terminal pattern for every version; only the `cd` path changes.

**v01 (simplest flow)**

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

Open [http://localhost:25001](http://localhost:25001) → **Start authorization** → log in as `user0` / `password0`.

Expected callback:

```
http://localhost:25001/callback?code=<random-string>
```

**v04 (full loop through protected API)**

Use `versions/v04-protected-resource/` instead of `v01` in the commands above.

After login you should land on **`/profile`** (display name and email), not a raw token on the callback page. Home shows logged-in state; **Log out** clears the client session.

Test the resource server directly:

```bash
curl -s http://localhost:25000/api/me \
  -H "Authorization: Bearer <access_token from /debug/state>"
```

## Learning resources

- [RFC 6749 — OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 — PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 6750 — Bearer Token Usage](https://datatracker.ietf.org/doc/html/rfc6750)
- [RFC 6749 §6 — Refreshing an Access Token](https://datatracker.ietf.org/doc/html/rfc6749#section-6) (v05)
- [OAuth 2.0 Simplified](https://www.oauth.com/)
