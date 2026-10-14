"""Verify a FoPost webhook delivery and read its envelope.

Every outbound FoPost webhook, including the Website blog target, is signed the
same way: ``X-FoPost-Signature-256`` is an HMAC-SHA256 over ``{timestamp}.{body}``
with ``X-FoPost-Timestamp`` beside it, and ``X-FoPost-Signature`` is the older
HMAC over the body alone. Pass the raw request bytes, never a re-serialised
object: a single reordered key changes the digest.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

__all__ = [
    "SIGNATURE_TOLERANCE_SECONDS",
    "WebhookEvent",
    "WebhookVerificationError",
    "verify",
    "verify_signature",
]

#: Refuse a delivery signed longer ago than this. Matches the API's own tolerance.
SIGNATURE_TOLERANCE_SECONDS = 300

_SIGNATURE_HEADER = "x-fopost-signature"
_TIMESTAMPED_SIGNATURE_HEADER = "x-fopost-signature-256"
_TIMESTAMP_HEADER = "x-fopost-timestamp"
_EVENT_HEADER = "x-fopost-event"


class WebhookVerificationError(Exception):
    """A delivery that could not be trusted.

    ``code`` is one of ``missing_secret``, ``invalid_signature``, ``stale_delivery``
    or ``invalid_body``.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class WebhookEvent:
    """The envelope every FoPost webhook carries."""

    event: str
    data: dict[str, Any]
    timestamp: str | None = None


def header(headers: Mapping[str, Any], name: str) -> str | None:
    """Read a header case-insensitively from a dict or a framework headers object."""
    getter = getattr(headers, "get", None)
    if getter is not None:
        value = getter(name)
        if value is None:
            value = getter(name.title())
        if value is not None:
            return value[0] if isinstance(value, (list, tuple)) else str(value)
    for key, value in dict(headers).items():
        if key.lower() == name:
            return value[0] if isinstance(value, (list, tuple)) else str(value)
    return None


def _digest(value: str | None) -> str | None:
    if value is None:
        return None
    return value[7:] if value.startswith("sha256=") else value


def verify_signature(
    body: str | bytes,
    headers: Mapping[str, Any],
    secret: str,
    *,
    tolerance: float = SIGNATURE_TOLERANCE_SECONDS,
) -> None:
    """Raise ``WebhookVerificationError`` when the delivery is unsigned, forged or stale.

    Prefers the timestamped ``X-FoPost-Signature-256`` and falls back to the
    body-only ``X-FoPost-Signature`` when no timestamp header is present.
    """
    if not secret:
        raise WebhookVerificationError("missing_secret", "A webhook secret is required")

    raw = body.encode() if isinstance(body, str) else body
    key = secret.encode()

    timestamped = _digest(header(headers, _TIMESTAMPED_SIGNATURE_HEADER))
    if timestamped is not None:
        try:
            sent_at = int(header(headers, _TIMESTAMP_HEADER) or "")
        except ValueError as err:
            raise WebhookVerificationError(
                "invalid_signature", "Signed delivery carries no timestamp"
            ) from err
        age = abs(time.time() - sent_at)
        if age > tolerance:
            raise WebhookVerificationError("stale_delivery", f"Delivery is {int(age)}s old")
        expected = hmac.new(key, f"{sent_at}.".encode() + raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(timestamped, expected):
            raise WebhookVerificationError("invalid_signature", "Signature does not match the body")
        return

    plain = _digest(header(headers, _SIGNATURE_HEADER))
    if plain is None:
        raise WebhookVerificationError("invalid_signature", "Delivery carries no signature header")
    if not hmac.compare_digest(plain, hmac.new(key, raw, hashlib.sha256).hexdigest()):
        raise WebhookVerificationError("invalid_signature", "Signature does not match the body")


def verify(
    body: str | bytes,
    headers: Mapping[str, Any],
    secret: str,
    *,
    tolerance: float = SIGNATURE_TOLERANCE_SECONDS,
) -> WebhookEvent:
    """Verify the signature and return the parsed ``{event, data, timestamp}`` envelope.

    ::

        from fopost import verify_webhook

        event = verify_webhook(request.body, request.headers, secret)
        if event.event == "article.published":
            article = ArticlePublishedPayload.model_validate(event.data)
    """
    verify_signature(body, headers, secret, tolerance=tolerance)

    raw = body.decode() if isinstance(body, bytes) else body
    try:
        envelope = json.loads(raw)
    except ValueError as err:
        raise WebhookVerificationError("invalid_body", "Webhook body is not JSON") from err
    if not isinstance(envelope, dict):
        raise WebhookVerificationError("invalid_body", "Webhook body is not an object")

    event = envelope.get("event") or header(headers, _EVENT_HEADER)
    if not isinstance(event, str) or not event:
        raise WebhookVerificationError("invalid_body", "Webhook body names no event")
    data = envelope.get("data")
    timestamp = envelope.get("timestamp")
    return WebhookEvent(
        event=event,
        data=data if isinstance(data, dict) else {},
        timestamp=timestamp if isinstance(timestamp, str) else None,
    )
