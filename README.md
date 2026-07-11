# OAuth 2 Learning Lab

Learn OAuth 2 by building it in versioned snapshots. Start with the simplest flow and add one security or protocol idea per version.

**v01–v05:** auth + resource on `:25000` · client on `:25001`  
**v06+:** auth (OpenID Provider from v07) on `:25000` · client on `:25001` · resource server on `:25002`

See [`.env.example`](.env.example) for defaults.

## Start here

**[v01 — Login and authorization code](https://sauvikbiswas.com/posts/learning-oauth-2-01/)** · [code](versions/v01-login-and-code/)

Minimal runnable server + client: login, issue a `code`, redirect to callback. No `state`, no PKCE, no token endpoint.

**Latest snapshot: [v10 — Token exchange (On-Behalf-Of)](https://sauvikbiswas.com/posts/learning-oauth-2-10/)** · [code](versions/v10-token-exchange/) *(scaffold)*  
Adds a fourth process — an agent on `:25003` that swaps a user token for a downstream resource token via [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693). Builds on v09 resource indicators and v08 JWKS.

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
| [v08](https://sauvikbiswas.com/posts/learning-oauth-2-08/) · [code](versions/v08-jwks-rs256/) | **available** | JWKS + RS256; drop shared `JWT_SECRET`; publish `jwks_uri`; client and resource server verify `id_token` (and JWT access tokens) with public keys |
| [v09](https://sauvikbiswas.com/posts/learning-oauth-2-09/) · [code](versions/v09-resource-indicators/) | **available** | [RFC 8707](https://datatracker.ietf.org/doc/html/rfc8707) resource indicators; `resource` binds tokens to `/api/resource-a` or `/api/resource-b` |
| [v10](https://sauvikbiswas.com/posts/learning-oauth-2-10/) · [code](versions/v10-token-exchange/) | **scaffold** | [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693) token exchange (On-Behalf-Of); agent on `:25003` swaps user token for downstream resource token |
| v11 | **planned** | MCP-style agent authorization; OAuth for AI tools calling protected APIs (dynamic client registration, delegation) |
| v12 | **planned** | Identity Assertion Authorization Grant ([ID-JAG](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-identity-assertion-authz-grant)) / [Cross App Access](https://www.okta.com/newsroom/press-releases/okta-announces-cross-app-access-partners/); cross-app enterprise SSO by exchanging an IdP identity assertion for another app's access token (extends v10 [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693)) |

**Intermission 1:** [What industry ships and who gets paid](https://sauvikbiswas.com/posts/learning-oauth-2-intermission-01/) — after v07; market research before the v08+ delegation arc.

**Intermission 2:** [Agents, consent, and the MCP authorization model](https://sauvikbiswas.com/posts/learning-oauth-2-intermission-02/) — after v10; bridges the delegation arc to the planned v11 MCP work.

v09–v12 are the current plan; version splits and ordering may change as snapshots land. Out of scope for the core lab path: enterprise SAML/SCIM, MFA/fraud, IGA/PAM, fine-grained AuthZ (ReBAC).

Diff adjacent versions to see exactly what changed:

```bash
diff -ru versions/v07-openid-connect versions/v08-jwks-rs256
```

## Quick start

**v01–v05:** two terminals (authorization + resource server on `:25000`, client on `:25001`).

**v06+:** three terminals (auth `:25000`, resource `:25002`, client `:25001`). **v10+** adds a fourth terminal (agent `:25003`). Copy [`.env.example`](.env.example) into each app directory (auth-server, resource-server, client, and agent for v10).

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

**v06+** (three-process split — use folder names from the [version roadmap](#version-roadmap); latest: `v08-jwks-rs256`)

```bash
# Terminal 1 — auth server / OpenID Provider
cd versions/v08-jwks-rs256/auth-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 2 — resource server
cd versions/v08-jwks-rs256/resource-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py

# Terminal 3 — client
cd versions/v08-jwks-rs256/client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

Open [http://localhost:25001](http://localhost:25001) → **Start authorization** → log in as `user0` / `password0`.

For any other version, replace the folder names from the [version roadmap](#version-roadmap). Each snapshot builds on the last; `diff -ru` adjacent folders to see what changed. Use `/debug/state` on each running app to inspect session and in-memory state.

## Learning resources

**Intermissions**

- [Intermission 1 — What industry ships and who gets paid](https://sauvikbiswas.com/posts/learning-oauth-2-intermission-01/) — after v07: vendors, pricing, M&A, and agent identity.
- [Intermission 2 — Agents, consent, and the MCP authorization model](https://sauvikbiswas.com/posts/learning-oauth-2-intermission-02/) — after v10: browser OAuth vs agent delegation, MCP discovery chain, threat model.

- [RFC 6749 — OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 — PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 6750 — Bearer Token Usage](https://datatracker.ietf.org/doc/html/rfc6750)
- [RFC 6749 §6 — Refreshing an Access Token](https://datatracker.ietf.org/doc/html/rfc6749#section-6)
- [RFC 7662 — Token Introspection](https://datatracker.ietf.org/doc/html/rfc7662) (v06 Mode A)
- [RFC 7519 — JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519) (v06 Mode B; v07 `id_token`)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) (v07)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html) (v07)
- [RFC 7517 — JSON Web Key (JWK)](https://datatracker.ietf.org/doc/html/rfc7517) (v08)
- [RFC 8707 — Resource Indicators](https://datatracker.ietf.org/doc/html/rfc8707) (v09)
- [RFC 8693 — Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693) (v10 scaffold)
- [MCP Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) (planned v11)
- [OAuth 2.0 Simplified](https://www.oauth.com/)
