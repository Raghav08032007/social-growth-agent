"""Envelope encryption bound to workspace/provider/account by AES-GCM associated data."""

import base64
import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select

from .models import AgentAction, VaultToken
from .security import Problem


def b64(value):
    return base64.urlsafe_b64encode(value).decode()


def unb64(value):
    return base64.b64decode(value, altchars=b"-_", validate=True)


class EnvironmentKeyProvider:
    """Replace with managed KMS before hosted production; key IDs enable safe rotation."""

    def __init__(self, keys, active):
        self.keys, self.active = keys, active

    def wrap(self, data_key, context):
        nonce = os.urandom(12)
        wrapped = AESGCM(self.keys[self.active]).encrypt(nonce, data_key, context)
        return {"key_id": self.active, "wrap_nonce": b64(nonce), "wrapped_key": b64(wrapped)}

    def unwrap(self, envelope, context):
        try:
            return AESGCM(self.keys[envelope["key_id"]]).decrypt(
                unb64(envelope["wrap_nonce"]), unb64(envelope["wrapped_key"]), context
            )
        except (KeyError, ValueError, InvalidTag, TypeError):
            raise Problem(
                "vault_unavailable", "Token cannot be decrypted with current keys", 503
            ) from None


class Vault:
    def __init__(self, provider):
        self.provider = provider

    @staticmethod
    def context(workspace, provider, account):
        return json.dumps([workspace, provider, account], separators=(",", ":")).encode()

    def store(self, db, workspace, provider, account, secret, scopes, actor="system"):
        if not isinstance(secret, str) or not secret or len(secret) > 16000:
            raise Problem("validation", "Token must be nonempty text within size limit")
        if db.scalar(
            select(VaultToken).where(
                VaultToken.workspace_id == workspace,
                VaultToken.provider == provider,
                VaultToken.account_id == account,
            )
        ):
            raise Problem("conflict", "Connection already exists; disconnect before replacing", 409)
        context = self.context(workspace, provider, account)
        data_key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
        envelope = self.provider.wrap(data_key, context)
        envelope.update(
            {
                "nonce": b64(nonce),
                "ciphertext": b64(AESGCM(data_key).encrypt(nonce, secret.encode(), context)),
            }
        )
        row = VaultToken(
            workspace_id=workspace,
            provider=provider,
            account_id=account,
            envelope=envelope,
            scopes=scopes,
        )
        db.add(row)
        db.flush()
        db.add(
            AgentAction(
                workspace_id=workspace, action="vault.stored", actor_id=actor, entity_id=row.id
            )
        )
        return row.id

    def row(self, db, workspace, token_id):
        row = db.scalar(
            select(VaultToken).where(
                VaultToken.id == token_id,
                VaultToken.workspace_id == workspace,
                VaultToken.revoked.is_(False),
            )
        )
        if row is None:
            raise Problem("not_found", "Connection not found", 404)
        return row

    def read(self, db, workspace, token_id):
        row = self.row(db, workspace, token_id)
        context = self.context(workspace, row.provider, row.account_id)
        data_key = self.provider.unwrap(row.envelope, context)
        try:
            return (
                AESGCM(data_key)
                .decrypt(unb64(row.envelope["nonce"]), unb64(row.envelope["ciphertext"]), context)
                .decode()
            )
        except (KeyError, ValueError, InvalidTag, UnicodeError, TypeError):
            raise Problem("vault_unavailable", "Token envelope failed verification", 503) from None

    def rewrap(self, db, workspace, token_id):
        row = self.row(db, workspace, token_id)
        context = self.context(workspace, row.provider, row.account_id)
        data_key = self.provider.unwrap(row.envelope, context)
        row.envelope = {**row.envelope, **self.provider.wrap(data_key, context)}
        db.add(
            AgentAction(
                workspace_id=workspace,
                action="vault.rewrapped",
                actor_id="system",
                entity_id=token_id,
            )
        )

    def revoke(self, db, workspace, token_id, actor):
        row = self.row(db, workspace, token_id)
        row.revoked = True
        row.envelope = {}
        db.add(
            AgentAction(
                workspace_id=workspace, action="vault.revoked", actor_id=actor, entity_id=token_id
            )
        )
