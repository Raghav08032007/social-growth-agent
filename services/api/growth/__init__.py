import uuid

from flask import Flask, g, jsonify, request
from redis.exceptions import RedisError
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from .config import Settings
from .costs import summary
from .db import make_engine, transaction
from .jobs import enqueue
from .models import (
    AgentAction,
    CreditEntry,
    FeatureFlag,
    Job,
    Membership,
    User,
    VaultToken,
    Workspace,
)
from .security import Problem, authenticate, membership
from .vault import EnvironmentKeyProvider, Vault


def create_app(settings=None):
    settings = settings or Settings.from_env()
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=16384)
    engine = make_engine(settings.database_url)
    app.extensions["engine"] = engine
    app.extensions["settings"] = settings
    app.extensions["vault"] = Vault(
        EnvironmentKeyProvider(settings.vault_keys, settings.active_key)
    )

    @app.before_request
    def request_context():
        g.request_id = uuid.uuid4().hex

    @app.after_request
    def headers(response):
        response.headers["X-Request-ID"] = g.request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.errorhandler(Problem)
    def problem(exc):
        return jsonify(
            error={"code": exc.code, "message": exc.message, "request_id": g.request_id}
        ), exc.status

    @app.errorhandler(HTTPException)
    def http_problem(exc):
        return problem(Problem("http_error", exc.name, exc.code))

    @app.errorhandler(Exception)
    def unexpected(exc):
        app.logger.error(
            "Unhandled request failure id=%s type=%s", g.request_id, type(exc).__name__
        )
        return problem(Problem("internal_error", "Request could not be completed", 500))

    def context(db):
        user = authenticate(db, request.headers.get("Authorization", ""))
        workspace = request.headers.get("X-Workspace-ID", "")
        member = membership(db, user.id, workspace)
        return user, workspace, member.role

    @app.get("/health/live")
    def live():
        return jsonify(status="alive")

    @app.get("/health/ready")
    def ready():
        try:
            with engine.connect() as db:
                db.execute(text("SELECT 1"))
                db.execute(text("SELECT version_num FROM alembic_version"))
            from redis import Redis

            Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2).ping()
        except (SQLAlchemyError, RedisError):
            return jsonify(status="unavailable"), 503
        return jsonify(status="ready")

    @app.get("/v1/workspaces")
    def workspaces():
        with transaction(engine) as db:
            user = authenticate(db, request.headers.get("Authorization", ""))
            rows = db.scalars(
                select(Workspace).join(Membership).where(Membership.user_id == user.id)
            )
            return jsonify(
                user={"id": user.id, "name": user.name, "is_staff": user.is_staff},
                workspaces=[{"id": row.id, "name": row.name} for row in rows],
            )

    @app.get("/v1/workspaces/current/<collection>")
    def collection(collection):
        with transaction(engine) as db:
            user, workspace, role = context(db)
            models = {
                "flags": FeatureFlag,
                "audit": AgentAction,
                "usage": CreditEntry,
                "jobs": Job,
                "connections": VaultToken,
            }
            model = models.get(collection)
            if model is None:
                raise Problem("not_found", "Collection not found", 404)
            try:
                limit = int(request.args.get("limit", "100"))
            except ValueError:
                raise Problem("validation", "limit must be an integer") from None
            cursor = request.args.get("after", "")
            if not 1 <= limit <= 100 or len(cursor) > 32:
                raise Problem("validation", "Invalid page limit or cursor")
            rows = list(
                db.scalars(
                    select(model)
                    .where(model.workspace_id == workspace, model.id > cursor)
                    .order_by(model.id)
                    .limit(limit + 1)
                )
            )
            has_more = len(rows) > limit
            rows = rows[:limit]
            fields = {
                "flags": ["id", "name", "enabled"],
                "audit": ["id", "action", "entity_id", "created_at"],
                "usage": ["id", "amount_paise", "category", "created_at"],
                "jobs": ["id", "kind", "status", "attempts", "available_at", "last_error"],
                "connections": ["id", "provider", "scopes", "revoked"],
            }[collection]
            return jsonify(
                items=[{key: getattr(row, key) for key in fields} for row in rows],
                next_cursor=rows[-1].id if has_more else None,
            )

    @app.get("/v1/workspaces/current/summary")
    def workspace_summary():
        with transaction(engine) as db:
            _user, workspace, _role = context(db)
            value = summary(db, db.get(Workspace, workspace))
            value["counts"] = {
                name: db.scalar(
                    select(func.count()).select_from(model).where(model.workspace_id == workspace)
                )
                for name, model in [
                    ("jobs", Job),
                    ("connections", VaultToken),
                    ("audit", AgentAction),
                ]
            }
            return jsonify(value)

    @app.post("/v1/jobs/diagnostic")
    def diagnostic():
        with transaction(engine) as db:
            user, workspace, role = context(db)
            if role not in {"owner", "manager"} or settings.environment == "production":
                raise Problem("forbidden", "Diagnostic jobs are disabled for this context", 403)
            payload = request.get_json()
            if not isinstance(payload, dict):
                raise Problem("validation", "JSON body must be an object")
            row = enqueue(
                db, workspace, request.headers.get("Idempotency-Key"), "diagnostic.retry", payload
            )
            return jsonify(id=row.id, status=row.status), 202

    @app.delete("/v1/session")
    def revoke_session():
        from .models import SessionToken
        from .security import digest

        with transaction(engine) as db:
            authenticate(db, request.headers.get("Authorization", ""))
            db.get(SessionToken, digest(request.headers["Authorization"][7:])).revoked = True
        return "", 204

    @app.get("/v1/admin/overview")
    def admin():
        with transaction(engine) as db:
            user = authenticate(db, request.headers.get("Authorization", ""))
            if not user.is_staff:
                raise Problem("forbidden", "Staff access required", 403)
            spaces = list(db.scalars(select(Workspace).order_by(Workspace.id).limit(100)))
            failed = db.scalars(select(Job).where(Job.status == "dead_letter").limit(100))
            users = db.scalars(select(User).limit(100))
            return jsonify(
                workspaces=[summary(db, workspace) for workspace in spaces],
                failed_jobs=[
                    {"id": row.id, "workspace_id": row.workspace_id, "last_error": row.last_error}
                    for row in failed
                ],
                users=[{"id": row.id, "name": row.name, "is_staff": row.is_staff} for row in users],
            )

    from .cli import register

    register(app)
    return app
