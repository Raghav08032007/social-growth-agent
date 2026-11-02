import hashlib
import secrets

from sqlalchemy import select

from .models import Membership, SessionToken, User, timestamp


class Problem(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(db, user_id, lifetime=3600):
    token = secrets.token_urlsafe(32)
    db.add(
        SessionToken(token_hash=digest(token), user_id=user_id, expires_at=timestamp() + lifetime)
    )
    return token


def authenticate(db, authorization):
    if not authorization.startswith("Bearer ") or len(authorization) > 256:
        raise Problem("unauthorized", "A valid session is required", 401)
    token = db.get(SessionToken, digest(authorization[7:]))
    if token is None or token.revoked or token.expires_at <= timestamp():
        raise Problem("unauthorized", "Session expired or revoked", 401)
    return db.get(User, token.user_id)


def membership(db, user_id, workspace_id):
    member = db.scalar(
        select(Membership).where(
            Membership.user_id == user_id, Membership.workspace_id == workspace_id
        )
    )
    if member is None:
        raise Problem("forbidden", "Workspace access denied", 403)
    return member
