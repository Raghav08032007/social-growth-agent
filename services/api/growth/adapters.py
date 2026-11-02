"""Provider contracts only. No production path silently substitutes a fake provider."""

from dataclasses import dataclass
from typing import Protocol

from .costs import record_cost
from .security import Problem


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int


def meter_model_usage(
    db, workspace, request_id, usage, *, input_paise_per_million, output_paise_per_million
):
    values = (
        usage.input_tokens,
        usage.output_tokens,
        input_paise_per_million,
        output_paise_per_million,
    )
    if any(type(value) is not int or value < 0 for value in values):
        raise Problem("validation", "Usage and configured prices must be nonnegative integers")
    # Round the combined cost up to the nearest paise, once per provider request.
    numerator = (
        usage.input_tokens * input_paise_per_million
        + usage.output_tokens * output_paise_per_million
    )
    return record_cost(db, workspace, request_id, (numerator + 999999) // 1000000, "ai")


class KeyProvider(Protocol):
    def wrap(self, data_key: bytes, context: bytes) -> dict: ...
    def unwrap(self, envelope: dict, context: bytes) -> bytes: ...


class ModelProvider(Protocol):
    def generate(self, request_id: str, prompt: str) -> tuple[str, ModelUsage]: ...


class MessageProvider(Protocol):
    def send(self, request_id: str, recipient: str, text: str) -> str: ...


class PaymentProvider(Protocol):
    def create_checkout(self, request_id: str, amount_paise: int, currency: str) -> str: ...


class ObjectStorage(Protocol):
    def put(self, workspace_id: str, name: str, body: bytes, content_type: str) -> str: ...
    def get(self, workspace_id: str, name: str) -> bytes: ...


@dataclass(frozen=True)
class Capability:
    provider: str
    action: str
    required_scopes: frozenset[str]
    source_url: str
    api_version: str
    verified: bool = False


class CapabilityRegistry:
    def __init__(self, capabilities=()):
        self.entries = {(entry.provider, entry.action): entry for entry in capabilities}

    def require(self, provider, action, granted_scopes):
        entry = self.entries.get((provider, action))
        if entry is None or not entry.verified:
            raise Problem(
                "capability_unavailable", "Action has not been verified for this provider", 503
            )
        if not entry.required_scopes <= set(granted_scopes):
            raise Problem("scope_denied", "Required connector permissions are missing", 403)
        return entry


class UnconfiguredProvider:
    def __getattr__(self, name):
        raise Problem(
            "provider_unavailable", "Provider credentials and a verified adapter are required", 503
        )
