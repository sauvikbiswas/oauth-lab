# OAuth 2 Learning Lab

Learn OAuth 2 by building it in versioned snapshots. Start with the simplest flow and add one security or protocol idea per version.

**v01–v05:** auth + resource on `:25000` · client on `:25001`  
**v06–v07:** auth (OpenID Provider) on `:25000` · client on `:25001` · resource server on `:25002`  

See [`.env.example`](.env.example) for defaults.

## Start here

**[v01 — Login and authorization code](https://sauvikbiswas.com/posts/learning-oauth-2-01/)** · [code](versions/v01-login-and-code/)

Minimal runnable server + client: login, issue a `code`, redirect to callback. No `state`, no PKCE, no token endpoint.

**Latest snapshot: [v07 — OpenID Connect](docs/learning-oauth-2-07/index.md)** · [code](versions/v07-openid-connect/)  
Same three-process layout as v06, plus OIDC: `id_token`, `nonce`, UserInfo, and discovery. Builds on v06 split validation (introspection or JWT access tokens).

Previous: [v06 — Split auth and resource servers](docs/learning-oauth-2-06/index.md) · [code](versions/v06-split-servers/)

## Version roadmap

| Version | Status | Adds |
|---------|--------|------|
| [v01](https://sauvikbiswas.com/posts/learning-oauth-2-01/) · [code](versions/v01-login-and-code/) | **available** | login + code redirect; param resume; client registry + `redirect_uri` validation |
| [v02](https://sauvikbiswas.com/posts/learning-oauth-2-02/) · [code](versions/v02-state-csrf/) | **available** | OAuth `state` (CSRF); client generates + verifies, server requires + pass-through |
| [v03](https://sauvikbiswas.com/posts/learning-oauth-2-03/) · [code](versions/v03-pkce/) | **available** | PKCE (`code_challenge` / `code_verifier`); `POST /token`; client code exchange |
| [v04](https://sauvikbiswas.com/posts/learning-oauth-2-04/) · [code](versions/v04-protected-resource/) | **available** | `GET /api/me` (Bearer); client session token; `/profile` and logout |
| [v05](https://sauvikbiswas.com/posts/learning-oauth-2-05/) · [code](versions/v05-refresh-token/) | **available** | refresh tokens; silent client refresh |
| [v06](https://sauvikbiswas.com/posts/learning-oauth-2-06/) · [code](versions/v06-split-servers/) | **available** | split auth server / resource server; `POST /introspect`; JWT or introspection validation; profile data on resource server |
| [v07](https://sauvikbiswas.com/posts/learning-oauth-2-07/) · [code](versions/v07-openid-connect/) | **available** | OpenID Connect on v06 split; `id_token`, `nonce`, UserInfo, discovery; `/profile` triptych (identity + API data) |

Diff adjacent versions to see exactly what changed:

```bash
diff -ru versions/v06-split-servers versions/v07-openid-connect
```

## Quick start

**v01–v05:** two terminals (authorization + resource server on `:25000`, client on `:25001`).

**v06–v07:** three terminals (auth `:25000`, resource `:25002`, client `:25001`). Copy [`.env.example`](.env.example) into each app directory (auth-server, resource-server, client).

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

**v07 (OpenID Connect — recommended starting point for split layout)**

```bash
# Terminal 1 — auth server / OpenID Provider
cd versions/v07-openid-connect/auth-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 2 — resource server
cd versions/v07-openid-connect/resource-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 3 — client
cd versions/v07-openid-connect/client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

**v06 (split servers, OAuth only)**

```bash
# Terminal 1 — auth server
cd versions/v06-split-servers/auth-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 2 — resource server
cd versions/v06-split-servers/resource-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 3 — client
cd versions/v06-split-servers/client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

Open [http://localhost:25001](http://localhost:25001) → **Start authorization** → log in as `user0` / `password0`.

For any other version, replace the folder names from the [version roadmap](#version-roadmap). Each snapshot builds on the last; `diff -ru` adjacent folders to see what changed. Use `/debug/state` on each running app to inspect session and in-memory state.

## Learning resources

**[Intermission — What industry ships and who gets paid](docs/learning-oauth-2-intermission-01/)** — market research pause after v07: vendors, pricing, M&A, and agent identity.

- [RFC 6749 — OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 — PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 6750 — Bearer Token Usage](https://datatracker.ietf.org/doc/html/rfc6750)
- [RFC 6749 §6 — Refreshing an Access Token](https://datatracker.ietf.org/doc/html/rfc6749#section-6)
- [RFC 7662 — Token Introspection](https://datatracker.ietf.org/doc/html/rfc7662) (v06 Mode A)
- [RFC 7519 — JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519) (v06 Mode B; v07 `id_token`)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) (v07)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html) (v07)
- [OAuth 2.0 Simplified](https://www.oauth.com/)
