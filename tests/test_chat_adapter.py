from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import httpx
import pytest
import respx

from fopost import Fopost
from fopost.chat_adapter import (
    INBOUND_EVENT,
    ChatAdapter,
    ChatAdapterError,
)
from tests.conftest import BASE_URL

SECRET = "whsec_test"

DM_FIXTURE: dict[str, Any] = {
    "id": "itm_1",
    "workspaceId": "ws_1",
    "platform": "instagram",
    "type": "dm",
    "state": "unread",
    "direction": "inbound",
    "conversationId": "conv_1",
    "authorName": "Sam Rivera",
    "authorHandle": "samrivera",
    "text": "Do you ship to Portugal?",
    "attachments": [],
    "platformCreatedAt": "2026-09-20T09:00:00.000Z",
    "createdAt": "2026-09-20T09:00:01.000Z",
    "canReply": True,
    "account": {"id": "acc_1", "platform": "instagram", "username": "yourbrand"},
}


def item(**over: Any) -> dict[str, Any]:
    return {**DM_FIXTURE, **over}


def adapter(client: Fopost) -> ChatAdapter:
    return ChatAdapter(client, workspace_id="ws_1", webhook_secret=SECRET)


def delivery(payload: dict[str, Any]) -> tuple[str, dict[str, str]]:
    body = json.dumps(
        {"event": INBOUND_EVENT, "data": payload, "timestamp": "2026-09-20T09:00:02.000Z"}
    )
    sent_at = int(time.time())
    sign = lambda message: hmac.new(  # noqa: E731
        SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return body, {
        "X-FoPost-Event": INBOUND_EVENT,
        "X-FoPost-Timestamp": str(sent_at),
        "X-FoPost-Signature": f"sha256={sign(body)}",
        "X-FoPost-Signature-256": f"sha256={sign(f'{sent_at}.{body}')}",
    }


@respx.mock
def test_round_trip_from_delivery_to_reply_to_read(client: Fopost) -> None:
    listing = respx.get(f"{BASE_URL}/inbox").mock(
        return_value=httpx.Response(
            200, json={"data": [item()], "meta": {"page": 1, "perPage": 25, "total": 1}}
        )
    )
    reply = respx.post(f"{BASE_URL}/inbox/itm_1/reply").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "item": item(
                        id="itm_2",
                        direction="outbound",
                        text="We do, in three to five days.",
                        state="read",
                    ),
                    "reply": {"externalId": "ig_9", "externalUrl": None},
                }
            },
        )
    )
    patch = respx.patch(f"{BASE_URL}/inbox/itm_1").mock(
        return_value=httpx.Response(200, json={"data": item(state="read")})
    )

    chat = adapter(client)
    body, headers = delivery(
        {
            "itemId": "itm_1",
            "type": "dm",
            "platform": "instagram",
            "accountId": "acc_1",
            "receivedAt": "2026-09-20T09:00:00.000Z",
        }
    )

    event = chat.parse_webhook(body, headers)
    assert (event.event, event.item_id, event.account_id) == (INBOUND_EVENT, "itm_1", "acc_1")

    message = chat.receive_one(event)
    assert message is not None
    assert message.text == "Do you ship to Portugal?"
    assert message.conversation_id == "conv_1"
    assert message.account_id == "acc_1"
    assert message.author.handle == "samrivera"

    sent = chat.send(reply_to=message.id, text="We do, in three to five days.")
    assert sent.id == "itm_2"
    assert sent.direction == "outbound"

    chat.mark_read(message)

    assert dict(listing.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "account_id": "acc_1",
        "type": "dm",
        "page": "1",
        "per_page": "25",
    }
    assert json.loads(reply.calls.last.request.content) == {"text": "We do, in three to five days."}
    assert json.loads(patch.calls.last.request.content) == {"state": "read"}


@respx.mock
def test_receive_reads_unread_inbound_dms(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/inbox").mock(
        return_value=httpx.Response(
            200, json={"data": [item()], "meta": {"page": 1, "perPage": 25, "total": 1}}
        )
    )
    messages = adapter(client).receive()
    assert len(messages) == 1
    params = dict(route.calls.last.request.url.params)
    assert params["type"] == "dm"
    assert params["direction"] == "inbound"
    assert params["state"] == "unread"


@respx.mock
def test_send_into_a_conversation_replies_to_its_newest_message(client: Fopost) -> None:
    listing = respx.get(f"{BASE_URL}/inbox").mock(
        return_value=httpx.Response(
            200, json={"data": [item()], "meta": {"page": 1, "perPage": 1, "total": 1}}
        )
    )
    respx.post(f"{BASE_URL}/inbox/itm_1/reply").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "item": item(id="itm_3", direction="outbound"),
                    "reply": {"externalId": None, "externalUrl": None},
                }
            },
        )
    )
    sent = adapter(client).send(conversation_id="conv_1", text="Still here.")
    assert sent.id == "itm_3"
    params = dict(listing.calls.last.request.url.params)
    assert params["conversation_id"] == "conv_1"
    assert params["sort"] == "newest"


@respx.mock
def test_send_by_handle_opens_a_conversation(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/inbox/conversations").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "conversationId": "conv_9",
                    "item": item(id="itm_9", direction="outbound"),
                }
            },
        )
    )
    sent = adapter(client).send(account_id="acc_1", handle="samrivera", text="Following up.")
    assert sent.id == "itm_9"
    assert json.loads(route.calls.last.request.content) == {
        "text": "Following up.",
        "account_id": "acc_1",
        "handle": "samrivera",
    }


@respx.mock
def test_receive_one_is_none_past_the_lookback(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/inbox").mock(
        return_value=httpx.Response(
            200, json={"data": [item(id="other")], "meta": {"page": 1, "perPage": 25, "total": 1}}
        )
    )
    assert adapter(client).receive_one("itm_gone") is None


@respx.mock
def test_a_forged_body_is_refused(client: Fopost) -> None:
    _, headers = delivery({"itemId": "itm_1", "accountId": "acc_1", "type": "dm"})
    with pytest.raises(ChatAdapterError) as err:
        adapter(client).parse_webhook('{"event":"inbox.message_received","data":{}}', headers)
    assert err.value.code == "invalid_signature"


@respx.mock
def test_a_delivery_outside_the_tolerance_is_refused(client: Fopost) -> None:
    body, headers = delivery({"itemId": "itm_1", "accountId": "acc_1", "type": "dm"})
    headers["X-FoPost-Timestamp"] = str(int(time.time()) - 4000)
    with pytest.raises(ChatAdapterError) as err:
        adapter(client).parse_webhook(body, headers)
    assert err.value.code == "stale_delivery"


@respx.mock
def test_the_compatibility_signature_still_verifies(client: Fopost) -> None:
    body, headers = delivery({"itemId": "itm_1", "accountId": "acc_1", "type": "dm"})
    del headers["X-FoPost-Signature-256"]
    assert adapter(client).parse_webhook(body, headers).item_id == "itm_1"


@respx.mock
def test_another_event_is_refused(client: Fopost) -> None:
    body = json.dumps({"event": "post.published", "data": {}, "timestamp": None})
    sent_at = int(time.time())
    signature = hmac.new(SECRET.encode(), f"{sent_at}.{body}".encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-FoPost-Timestamp": str(sent_at),
        "X-FoPost-Signature-256": f"sha256={signature}",
    }
    with pytest.raises(ChatAdapterError) as err:
        adapter(client).parse_webhook(body, headers)
    assert err.value.code == "unexpected_event"


def test_verification_needs_a_secret(client: Fopost) -> None:
    with pytest.raises(ChatAdapterError) as err:
        ChatAdapter(client).parse_webhook("{}", {})
    assert err.value.code == "missing_secret"
