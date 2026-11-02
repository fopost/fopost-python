from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import pytest

from fopost import WebhookVerificationError, verify_webhook, webhooks

SECRET = "whsec_test"

PAYLOAD: dict[str, Any] = {"id": "post_1", "status": "published"}


def _sign(message: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()


def delivery(sent_at: int | None = None) -> tuple[bytes, dict[str, str]]:
    body = json.dumps(
        {"event": "post.published", "data": PAYLOAD, "timestamp": "2026-10-10T09:00:01.000Z"}
    ).encode()
    sent_at = int(time.time()) if sent_at is None else sent_at
    return body, {
        "X-FoPost-Event": "post.published",
        "X-FoPost-Delivery": "dlv_1",
        "X-FoPost-Timestamp": str(sent_at),
        "X-FoPost-Signature": _sign(body),
        "X-FoPost-Signature-256": _sign(f"{sent_at}.".encode() + body),
    }


def test_a_timestamped_signature_passes_and_the_envelope_is_parsed() -> None:
    body, headers = delivery()
    event = verify_webhook(body, headers, SECRET)
    assert event.event == "post.published"
    assert event.timestamp == "2026-10-10T09:00:01.000Z"
    assert event.data == PAYLOAD


def test_the_module_path_is_the_same_helper() -> None:
    body, headers = delivery()
    assert webhooks.verify(body, headers, SECRET) == verify_webhook(body, headers, SECRET)


def test_a_tampered_body_fails() -> None:
    body, headers = delivery()
    tampered = body.replace(b"post_1", b"post_2")
    with pytest.raises(WebhookVerificationError) as err:
        verify_webhook(tampered, headers, SECRET)
    assert err.value.code == "invalid_signature"


def test_a_stale_timestamp_fails() -> None:
    body, headers = delivery(sent_at=int(time.time()) - 301)
    with pytest.raises(WebhookVerificationError) as err:
        verify_webhook(body, headers, SECRET)
    assert err.value.code == "stale_delivery"


def test_the_body_only_signature_passes_without_a_timestamp() -> None:
    body, headers = delivery()
    del headers["X-FoPost-Signature-256"]
    del headers["X-FoPost-Timestamp"]
    assert verify_webhook(body, headers, SECRET).event == "post.published"


def test_the_body_only_signature_is_ignored_when_the_timestamped_one_is_present() -> None:
    body, headers = delivery()
    headers["X-FoPost-Signature-256"] = _sign(b"0." + body)
    with pytest.raises(WebhookVerificationError) as err:
        verify_webhook(body, headers, SECRET)
    assert err.value.code == "invalid_signature"


def test_header_lookup_is_case_insensitive() -> None:
    body, headers = delivery()
    lowered = {key.lower(): value for key, value in headers.items()}
    assert verify_webhook(body.decode(), lowered, SECRET).event == "post.published"


def test_a_missing_secret_is_refused() -> None:
    body, headers = delivery()
    with pytest.raises(WebhookVerificationError) as err:
        verify_webhook(body, headers, "")
    assert err.value.code == "missing_secret"
