"""Foundation read diagnostic: 10k tenant jobs, 100 HTTP requests, ten concurrent clients."""

import hashlib
import json
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import insert

from growth import create_app
from growth.db import transaction
from growth.models import Job, Membership, User, Workspace, timestamp
from growth.security import issue_session

app = create_app()
engine = app.extensions["engine"]
with transaction(engine) as db:
    w = Workspace(name="Load diagnostic " + uuid.uuid4().hex[:8])
    u = User(name="Load diagnostic")
    db.add_all([w, u])
    db.flush()
    wid = w.id
    db.add(Membership(user_id=u.id, workspace_id=wid, role="owner"))
    token = issue_session(db, u.id)
    db.execute(
        insert(Job),
        [
            dict(
                id=uuid.uuid4().hex,
                workspace_id=wid,
                created_at=timestamp(),
                idempotency_key=hashlib.sha256(f"{wid}-{i}".encode()).hexdigest(),
                kind="diagnostic.retry",
                payload={"fail_until": 0},
                status="succeeded",
                attempts=1,
                max_attempts=3,
                available_at=0,
                lease_until=0,
            )
            for i in range(10000)
        ],
    )


def read(_):
    start = time.perf_counter()
    request = urllib.request.Request(
        "http://api:5000/v1/workspaces/current/jobs?limit=50",
        headers={"Authorization": "Bearer " + token, "X-Workspace-ID": wid},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.load(response)
        assert len(data["items"]) == 50 and data["next_cursor"]
    return (time.perf_counter() - start) * 1000


try:
    with ThreadPoolExecutor(max_workers=10) as pool:
        durations = sorted(pool.map(read, range(100)))
    p95 = durations[94]
    print(
        json.dumps(
            {
                "requests": 100,
                "concurrency": 10,
                "tenant_rows": 10000,
                "p95_ms": round(p95, 2),
                "target_ms": 300,
                "target_met": p95 < 300,
            }
        )
    )
    assert p95 < 300, "Foundation read p95 target exceeded"
finally:
    request = urllib.request.Request(
        "http://api:5000/v1/session", method="DELETE", headers={"Authorization": "Bearer " + token}
    )
    urllib.request.urlopen(request, timeout=5).close()
