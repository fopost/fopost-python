from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

ENDPOINT = {
    "id": "wh_1",
    "workspace_id": "ws_1",
    "name": "Prod",
    "url": "https://yourbrand.com/hooks/fopost",
    "events": ["post.published"],
    "header_names": ["X-Env"],
    "active": True,
    "last_triggered_at": None,
    "failure_count": 0,
    "created_at": "2026-10-18T12:00:00.000Z",
}

DELIVERY = {
    "id": "del_1",
    "webhook_id": "wh_1",
    "event": "post.published",
    "delivery_key": "post.published:post_1",
    "attempt": 1,
    "status": "failed",
    "response_status": 500,
    "response_snippet": "boom",
    "duration_ms": 120,
    "payload_hash": "abc",
    "next_retry_at": None,
    "created_at": "2026-10-18T12:00:00.000Z",
}


@respx.mock
def test_crud_and_test_send_the_expected_bodies(client: Fopost) -> None:
    listed = respx.get(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(200, json={"data": [ENDPOINT]})
    )
    created = respx.post(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(201, json={**ENDPOINT, "secret": "whsec_1"})
    )
    updated = respx.put(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"data": {**ENDPOINT, "active": False}})
    )
    deleted = respx.delete(f"{BASE_URL}/webhooks/wh_1").mock(return_value=httpx.Response(204))
    tested = respx.post(f"{BASE_URL}/webhooks/wh_1/test").mock(
        return_value=httpx.Response(200, json={"message": "sent"})
    )

    assert [w.id for w in client.webhook_endpoints.list()] == ["wh_1"]
    assert listed.called

    endpoint = client.webhook_endpoints.create(
        workspace_id="ws_1",
        url="https://yourbrand.com/hooks/fopost",
        events=["post.published"],
        name="Prod",
        headers={"X-Env": "prod"},
    )
    assert endpoint.secret == "whsec_1"
    assert endpoint.header_names == ["X-Env"]
    assert json.loads(created.calls.last.request.content) == {
        "workspaceId": "ws_1",
        "url": "https://yourbrand.com/hooks/fopost",
        "events": ["post.published"],
        "name": "Prod",
        "headers": {"X-Env": "prod"},
    }

    paused = client.webhook_endpoints.update("wh_1", active=False, headers=None)
    assert paused.active is False
    assert json.loads(updated.calls.last.request.content) == {"active": False, "headers": None}

    client.webhook_endpoints.delete("wh_1")
    client.webhook_endpoints.test("wh_1")
    assert deleted.called and tested.called


@respx.mock
def test_deliveries_are_listed_read_and_redelivered(client: Fopost) -> None:
    listed = respx.get(f"{BASE_URL}/webhooks/wh_1/deliveries").mock(
        return_value=httpx.Response(200, json={"data": [DELIVERY]})
    )
    respx.get(f"{BASE_URL}/webhooks/wh_1/deliveries/del_1").mock(
        return_value=httpx.Response(200, json={**DELIVERY, "payload": {"event": "post.published"}})
    )
    redelivered = respx.post(f"{BASE_URL}/webhooks/wh_1/deliveries/del_1/redeliver").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    deliveries = client.webhook_endpoints.deliveries("wh_1", status="failed", limit=10)
    assert deliveries[0].response_status == 500 and deliveries[0].payload is None
    assert dict(listed.calls.last.request.url.params) == {"status": "failed", "limit": "10"}

    one = client.webhook_endpoints.get_delivery("wh_1", "del_1")
    assert one.payload == {"event": "post.published"}

    client.webhook_endpoints.redeliver("wh_1", "del_1")
    assert redelivered.called
