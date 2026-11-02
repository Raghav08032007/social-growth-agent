# Working agreement

Read README.md, docs/delivery.md and the feature guide before implementation. This repository currently contains a plan and local demo. Do not report production parity or completed roadmap phases.

Preserve original feature IDs and phase assignments in docs/features.csv. A new feature starts with a specific specification and acceptance criteria; do not infer completion from generic tests. Keep fixture, browser, provider-sandbox and live evidence distinct.

Production direction is React/Vite/TypeScript + Flask + MySQL + Redis/Celery. The stdlib/SQLite app is deliberately local only. Never expose its workspace-header mechanism as authentication. Use official APIs/licensed data for production connectors, check capabilities and require approval for external actions as defined by the product policy.

Every production data path, background job, export and storage object needs tenant-aware authorization. Every retriable side effect needs idempotency/reconciliation. Money uses integer minor units, original references and append-only reversals. Record manual attribution honestly. Secrets, customer data, original private attachments and raw competitor page captures do not belong in public Git history.

Run the meaningful backend tests, catalogue validator and JS syntax checks after relevant changes. Update delivery status and material limits. Do not invent provider success, prices, legal requirements, market statistics or model availability. Explain irreversible actions and capability-dependent undo accurately.
