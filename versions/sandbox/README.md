# Sandbox — advanced work-in-progress

Personal playground for experimenting ahead of the versioned tutorial. Roughly **v05-level** on the server (state, PKCE, client registry, error pages, param stash); client is still mostly TODO stubs.

This folder is **not** a frozen tutorial snapshot — code here may be incomplete or in flux. When a feature stabilizes, it gets extracted into a numbered version (v02, v03, …).

## Run it

**Terminal 1 — server:**

```bash
cd versions/sandbox/server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

**Terminal 2 — client:**

```bash
cd versions/sandbox/client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../../.env.example .env
python3 app.py
```

Server: [http://localhost:25000](http://localhost:25000) · Client: [http://localhost:25001](http://localhost:25001)

## Guided path

For step-by-step learning, start with [v01 — Login and authorization code](../v01-login-and-code/README.md).
