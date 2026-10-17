from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import pytest

from fopost import ArticlePublishedPayload, WebhookVerificationError, verify_webhook, webhooks

SECRET = "whsec_test"

PAYLOAD: dict[str, Any] = {
    "id": "art_1",
    "title": "The Best Trail Running Shoes of the Year",
    "slug": "best-trail-running-shoes",
    "excerpt": None,
    "metaTitle": None,
    "metaDescription": None,
    "bodyMarkdown": "# Shoes",
    "bodyHtml": "<h1>Shoes</h1>",
    "featuredImage": {"mediaId": "med_1", "url": "https://cdn.test/f.jpg", "alt": "Trail"},
    "images": [{"mediaId": "med_2", "url": "https://cdn.test/1.jpg", "alt": "Mud", "position": 0}],
    "tags": ["shoes"],
    "keyword": "trail shoes",
    "wordCount": 1240,
    "publishedAt": "2026-10-10T09:00:00.000Z",
    "publishedUrl": "https://yourbrand.com/blog/best-trail-running-shoes",
}


def _sign(message: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()


def delivery(sent_at: int | None = None) -> tuple[bytes, dict[str, str]]:
    body = json.dumps(
        {"event": "article.published", "data": PAYLOAD, "timestamp": "2026-10-10T09:00:01.000Z"}
    ).encode()
    sent_at = int(time.time()) if sent_at is None else sent_at
    return body, {
        "X-FoPost-Event": "article.published",
        "X-FoPost-Delivery": "dlv_1",
        "X-FoPost-Timestamp": str(sent_at),
        "X-FoPost-Signature": _sign(body),
        "X-FoPost-Signature-256": _sign(f"{sent_at}.".encode() + body),
    }


def test_a_timestamped_signature_passes_and_the_envelope_is_parsed() -> None:
    body, headers = delivery()
    event = verify_webhook(body, headers, SECRET)
    assert event.event == "article.published"
    assert event.timestamp == "2026-10-10T09:00:01.000Z"
    article = ArticlePublishedPayload.model_validate(event.data)
    assert article.slug == "best-trail-running-shoes"
    assert article.featured_image is not None and article.featured_image.media_id == "med_1"
    assert article.images[0].position == 0
    assert article.published_url == "https://yourbrand.com/blog/best-trail-running-shoes"


def test_the_module_path_is_the_same_helper() -> None:
    body, headers = delivery()
    assert webhooks.verify(body, headers, SECRET) == verify_webhook(body, headers, SECRET)


def test_a_tampered_body_fails() -> None:
    body, headers = delivery()
    tampered = body.replace(b"best-trail", b"worst-trail")
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
    assert verify_webhook(body, headers, SECRET).event == "article.published"


def test_the_body_only_signature_is_ignored_when_the_timestamped_one_is_present() -> None:
    body, headers = delivery()
    headers["X-FoPost-Signature-256"] = _sign(b"0." + body)
    with pytest.raises(WebhookVerificationError) as err:
        verify_webhook(body, headers, SECRET)
    assert err.value.code == "invalid_signature"


def test_header_lookup_is_case_insensitive() -> None:
    body, headers = delivery()
    lowered = {key.lower(): value for key, value in headers.items()}
    assert verify_webhook(body.decode(), lowered, SECRET).event == "article.published"


def test_a_missing_secret_is_refused() -> None:
    body, headers = delivery()
    with pytest.raises(WebhookVerificationError) as err:
        verify_webhook(body, headers, "")
    assert err.value.code == "missing_secret"
