# OAuth 2 Learning Lab

Learn OAuth 2 by building it in versioned snapshots. Start with the simplest flow and add one security or protocol idea per version.

Auth server: `:25000` · Client: `:25001` (see [`.env.example`](.env.example)).

## Start here

**[v01 — Login and authorization code](https://sauvikbiswas.com/posts/learning-oauth-2-01/)** · [code](versions/v01-login-and-code/)

Minimal runnable server + client: login, issue a `code`, redirect to callback. No `state`, no PKCE, no token endpoint.

**Latest snapshot: [v05 — Refresh tokens](https://sauvikbiswas.com/posts/learning-oauth-2-05/)** · [code](versions/v05-refresh-token/)  
Everything in v04, plus short-lived access tokens, `grant_type=refresh_token`, and silent client refresh when `/api/me` returns 401.

## Version roadmap

| Version | Status | Adds |
|---------|--------|------|
| [v01](https://sauvikbiswas.com/posts/learning-oauth-2-01/) · [code](versions/v01-login-and-code/) | **available** | login + code redirect; param resume; client registry + `redirect_uri` validation |
| [v02](https://sauvikbiswas.com/posts/learning-oauth-2-02/) · [code](versions/v02-state-csrf/) | **available** | OAuth `state` (CSRF); client generates + verifies, server requires + pass-through |
| [v03](https://sauvikbiswas.com/posts/learning-oauth-2-03/) · [code](versions/v03-pkce/) | **available** | PKCE (`code_challenge` / `code_verifier`); `POST /token`; client code exchange |
| [v04](https://sauvikbiswas.com/posts/learning-oauth-2-04/) · [code](versions/v04-protected-resource/) | **available** | `GET /api/me` (Bearer); client session token; `/profile` and logout |
| [v05](https://sauvikbiswas.com/posts/learning-oauth-2-05/) · [code](versions/v05-refresh-token/) | **available** | refresh tokens; silent client refresh |

Diff adjacent versions to see exactly what changed:

```bash
diff -ru versions/v04-protected-resource versions/v05-refresh-token
```

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

For any other version, replace `v01-login-and-code` with the matching folder from the [version roadmap](#version-roadmap) in both terminal commands. Each snapshot builds on the last — `diff -ru` adjacent folders to see exactly what changed. Use the client home page and `/debug/state` on both apps (`:25001` and `:25000`) to inspect session and in-memory state.

## Learning resources

- [RFC 6749 — OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 — PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 6750 — Bearer Token Usage](https://datatracker.ietf.org/doc/html/rfc6750)
- [RFC 6749 §6 — Refreshing an Access Token](https://datatracker.ietf.org/doc/html/rfc6749#section-6)
- [OAuth 2.0 Simplified](https://www.oauth.com/)
