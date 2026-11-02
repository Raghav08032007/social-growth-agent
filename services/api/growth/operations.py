"""Operational records contain no request bodies, headers, query strings or exception text."""

from sqlalchemy import select

from .db import transaction
from .models import ApiError
from .security import Problem


def record_api_error(engine, request_id, route, method, status, code):
    with transaction(engine) as db:
        db.add(
            ApiError(
                request_id=request_id,
                route=route[:160],
                method=method[:10],
                status=status,
                code=code[:60],
            )
        )


def page(db, model, args, predicate=None):
    try:
        limit = int(args.get("limit", "50"))
    except (TypeError, ValueError):
        raise Problem("validation", "limit must be an integer") from None
    after = args.get("after", "")
    if not 1 <= limit <= 100 or len(after) > 32:
        raise Problem("validation", "Invalid page limit or cursor")
    query = select(model).where(model.id > after).order_by(model.id).limit(limit + 1)
    if predicate is not None:
        query = query.where(predicate)
    rows = list(db.scalars(query))
    more = len(rows) > limit
    return rows[:limit], rows[limit - 1].id if more else None
