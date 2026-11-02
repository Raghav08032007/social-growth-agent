# Phase 0 foundation — developer setup

The original local demo remains at `backend/` + `web/`. The new foundation is `services/api/` + `frontend/`. It has no public signup or real social/payment connections.

## Container stack

Requires running Docker Desktop with Linux containers. From the repository root:

```powershell
python scripts/init_local.py
docker compose up --build -d
docker compose exec api flask --app growth provision --name "Your name" --workspace "Your business" --staff
```

Open http://127.0.0.1:8080 and enter the session printed once by the provisioning command. `--staff` is for a trusted local operator; omit it for ordinary workspace owners. Each provision call creates a distinct workspace/user. Sessions expire after one hour; obtain another with `flask --app growth session --user-id ID` from the trusted operator terminal. No plaintext session is stored in the database or browser storage.

`scripts/init_local.py` creates random local MySQL passwords and a 32-byte vault key in the ignored `.env`. It never replaces existing keys. Do not delete `.env` after storing real secrets; key loss makes encrypted tokens unrecoverable. This Compose stack binds API/frontend ports to loopback and is a development environment, not a hosted production deployment.

```powershell
docker compose exec api python check_stack.py
docker compose ps
docker compose down
```

The diagnostic creates uniquely named fixture records, a cost fixture and two jobs. It verifies MySQL, Redis atomic limits, real Celery retry/dead-letter outcomes, vault rewrapping/revocation and a staff cost alert. It sends no real messages, makes no model call and moves no money. Fixture audit/cost records are retained intentionally; the session is revoked after a successful run. Do not use `down -v` casually: it deletes persistent data.

## Local API development

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r services/api/requirements-lock.txt
```

Set `DATABASE_URL`, `REDIS_URL`, `VAULT_KEYS` (JSON object of base64 32-byte keys), `VAULT_ACTIVE_KEY`, and `APP_ENV`. Use MySQL for development integration; SQLite is for fast tests. From `services/api`:

```powershell
alembic upgrade head
flask --app growth provision --name "Owner" --workspace "Business"
flask --app growth run --host 127.0.0.1 --port 5000
celery -A growth.worker:celery worker --loglevel=WARNING
celery -A growth.worker:celery beat --schedule=celerybeat-schedule
```

Prefer the Linux containers for workers. Run a single beat scheduler per environment; duplicate deliveries are fenced but duplicate schedulers waste broker capacity. No HTTP startup path creates schema automatically. `/health/live` is liveness; `/health/ready` requires database schema and Redis availability.

Frontend: `cd frontend`, `npm ci`, `npm run dev`; Vite proxies `/v1` and `/health` to port 5000. Session token stays only in React memory; a page reload clears it. The shell provides initial en/ta/hi strings and dark/light theme. Native-language review, offline support and full accessibility review remain open.

## Checks

```powershell
cd services/api
python -m pytest -q --cov=growth
ruff check growth tests
cd ../../frontend
npm run build
```

The optional `scripts/run_foundation_browser.py` uses project-local Playwright and intercepted transport to actual Flask handlers over temporary SQLite. Run `npx playwright install chromium` from `frontend`, then run the script with the API virtual environment. Alternatively set `CHROME_PATH` to an installed Chrome executable; `PLAYWRIGHT_MODULE` can override the library path. It checks credentials, staff alert/denial, languages, theme, preview isolation, motion/reduced-motion, content states, mobile/tablet reflow and session revocation. It does not certify direct browser HTTP or MySQL integration.

## Vault rotation

Add a new key ID to `VAULT_KEYS` while retaining the old key; set `VAULT_ACTIVE_KEY` to the new ID and recreate API/worker/scheduler. Run `flask --app growth rotate-vault`. The transaction rewraps per-record data keys while preserving token ciphertext. Verify decryption before retiring the old key, including backups still encrypted with it. Internal `Vault.revoke` erases the local envelope; remote provider revocation/refresh will require actual connectors in P1 and is not claimed here.

## API boundaries

An operator can configure monitoring with `flask --app growth configure-cost-policy --workspace-id ID --plan-price-paise 149900 --alert-percent 30`. This changes cost-alert assumptions only; it does not alter subscription billing or entitlements.

Bearer sessions authenticate users. `X-Workspace-ID` selects a workspace only after membership validation; it never authenticates. Collection reads are tenant scoped, return at most 100 rows, and support `limit`/`after` cursors. `/summary` provides uncapped counts and UTC-calendar-month AI cost. Only explicit staff users can access global operational summaries; global admin lists currently cap at 100 records and require pagination before large deployment.

Diagnostics are disabled when `APP_ENV=production`. Production settings require MySQL but do not by themselves establish production readiness. Managed key infrastructure, real connectors, security review and restore verification remain release gates. See `reports/phase-0.md` for the measured state.
