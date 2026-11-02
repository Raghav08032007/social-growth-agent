# Local reference API

Run `python backend/server.py` from the repository root. Requires Python 3.11+ and no packages. Binds only to `127.0.0.1:8000`; never expose it through a tunnel or public deployment. Run tests with `python -m unittest discover -s backend -p "test_*.py" -v`.

Open `http://127.0.0.1:8000/` for the web interface. The server serves only `web/index.html`, `web/app.js` and `web/styles.css` through an exact URL allowlist; repository documents, sources and database files are not served. Data starts empty so the first workflow can be completed explicitly.

This is a local demonstration using SQLite, without authentication, OAuth, AI, workers, real social publishing, messaging, payment collection or provider webhooks. `X-Workspace-ID: demo-a` (default) or `demo-b` chooses a known demonstration workspace; it is not a production authorization mechanism. Amounts are integer paise; financial entries are manually simulated associations, not verified causal attribution.

GET `/api/state` returns posts, leads, sales, immutable ledger, audit, and dashboard. POST `/api/posts` accepts caption, platform (instagram/facebook), language (en/ta/hi). POST `/api/posts/{id}/approve` then `/api/posts/{id}/publish` transitions the workflow. POST `/api/leads` accepts name, optional phone and post_id. POST `/api/sales` accepts post_id, optional lead_id, amount_paise and idempotency_key. POST `/api/sales/{id}/refund` accepts idempotency_key and reverses the full amount exactly once. Reusing an identical financial request key returns its original response; changing its payload returns 409.

Persistent data is in ignored `backend/demo.sqlite3`. Set DEMO_DB_PATH to another local path if needed. Data starts empty. Audit logs omit captions, phone numbers and names. The public-site investigation does not establish proprietary backend behavior; this API implements our proposed workflow.
