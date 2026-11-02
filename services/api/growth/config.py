"""Validated settings. Secrets have no source-controlled defaults."""

import base64
import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    vault_keys: dict[str, bytes]
    active_key: str
    environment: str = "development"

    @classmethod
    def from_env(cls):
        database = os.environ.get("DATABASE_URL", "")
        redis = os.environ.get("REDIS_URL", "")
        active = os.environ.get("VAULT_ACTIVE_KEY", "")
        environment = os.environ.get("APP_ENV", "development")
        if environment not in {"development", "testing", "production"}:
            raise ValueError("Invalid APP_ENV")
        try:
            keys = {
                name: base64.b64decode(value, altchars=b"-_", validate=True)
                for name, value in json.loads(os.environ.get("VAULT_KEYS", "{}")).items()
            }
        except (ValueError, TypeError, AttributeError):
            raise ValueError("VAULT_KEYS must be a JSON object of base64 keys") from None
        if not keys or active not in keys or any(len(key) != 32 for key in keys.values()):
            raise ValueError("Configure a 32-byte vault key and matching VAULT_ACTIVE_KEY")
        if not database or not redis.startswith(("redis://", "rediss://")):
            raise ValueError("DATABASE_URL and REDIS_URL are required")
        if environment == "production" and not database.startswith("mysql+pymysql://"):
            raise ValueError("Production requires MySQL")
        return cls(database, redis, keys, active, environment)
