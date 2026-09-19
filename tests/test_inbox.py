from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost, InboxItem
from tests.conftest import BASE_URL

ITEM_FIXTURE = {
    "id": "item_1",
    "workspaceId": "ws_1",
    "platform": "instagram",
    "type": "comment",
    "state": "unread",
    "direction": "inbound",
    "authorName": "Sam Rivera",
    "text": "Does this come in blue?",
    "attachments": [{"kind": "image", "url": "/v1/inbox/item_1/attachments/0"}],
    "platformCreatedAt": "2026-09-18T14:30:00.000Z",
    "canReply": True,
    "canHide": True,
    "canDelete": False,
    "post": {"id": "post_1", "title": "Autumn drop"},
    "account": {"id": "acc_1", "platform": "instagram", "username": "yourbrand"},
}


@respx.mock
def test_list_sends_snake_case_filters_and_keeps_meta(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/inbox").mock(
        return_value=httpx.Response(
            200, json={"data": [ITEM_FIXTURE], "meta": {"page": 2, "perPage": 10, "total": 11}}
        )
    )

    page = client.inbox.list(workspace_id="ws_1", state="unread", post_external_id="17895", page=2)

    assert len(page) == 1
    assert isinstance(page[0], InboxItem)
    assert page[0].author_name == "Sam Rivera"
    assert page[0].attachments[0].url == "/v1/inbox/item_1/attachments/0"
    assert page[0].can_reply is True
    assert page.meta.total == 11
    assert page.meta.per_page == 10
    assert dict(route.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "state": "unread",
        "post_external_id": "17895",
        "page": "2",
        "per_page": "25",
    }
    assert route.calls.last.request.headers["x-api-key"] == "osk_test_key"


@respx.mock
def test_reply_patch_and_moderation_hit_the_item_routes(client: Fopost) -> None:
    reply = respx.post(f"{BASE_URL}/inbox/item_1/reply").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "item": {**ITEM_FIXTURE, "state": "resolved"},
                    "reply": {"externalId": "c_9", "externalUrl": None},
                }
            },
        )
    )
    patch = respx.patch(f"{BASE_URL}/inbox/item_1").mock(
        return_value=httpx.Response(200, json={"data": {**ITEM_FIXTURE, "state": "snoozed"}})
    )
    hide = respx.post(f"{BASE_URL}/inbox/item_1/hide").mock(
        return_value=httpx.Response(200, json={"data": {**ITEM_FIXTURE, "hidden": True}})
    )
    delete = respx.delete(f"{BASE_URL}/inbox/item_1").mock(
        return_value=httpx.Response(200, json={"data": {"deleted": True}})
    )

    result = client.inbox.reply("item_1", "It does.")
    assert result.item.state == "resolved"
    assert result.reply["externalId"] == "c_9"
    assert json.loads(reply.calls.last.request.content) == {"text": "It does."}

    item = client.inbox.update("item_1", state="snoozed", snoozed_until="2030-01-01T00:00:00Z")
    assert item.state == "snoozed"
    assert json.loads(patch.calls.last.request.content) == {
        "state": "snoozed",
        "snoozedUntil": "2030-01-01T00:00:00Z",
    }

    assert client.inbox.hide("item_1").hidden is True
    assert hide.called
    client.inbox.delete("item_1")
    assert delete.called


@respx.mock
def test_thread_read_refresh_and_approvals(client: Fopost) -> None:
    read = respx.post(f"{BASE_URL}/inbox/read").mock(
        return_value=httpx.Response(200, json={"data": {"updated": 3}})
    )
    refresh = respx.post(f"{BASE_URL}/inbox/refresh").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"accountsPolled": 2, "newItems": 1, "rateLimited": 0, "dmReconnect": []}
            },
        )
    )
    approvals = respx.get(f"{BASE_URL}/inbox/approvals").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 7,
                        "workspaceId": "ws_1",
                        "source": "automation",
                        "reply": "Thanks!",
                        "createdAt": "2026-09-18T15:00:00.000Z",
                        "item": None,
                    }
                ]
            },
        )
    )
    approve = respx.post(f"{BASE_URL}/inbox/approvals/7/approve").mock(
        return_value=httpx.Response(200, json={"data": {"id": 7, "outcome": "sent"}})
    )
    unread = respx.get(f"{BASE_URL}/inbox/unread-count").mock(
        return_value=httpx.Response(200, json={"count": 4})
    )

    assert (
        client.inbox.mark_thread_read(workspace_id="ws_1", account_id="acc_1", conversation_id="c1")
        == 3
    )
    assert json.loads(read.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "account_id": "acc_1",
        "conversation_id": "c1",
    }

    polled = client.inbox.refresh(workspace_id="ws_1")
    assert polled.accounts_polled == 2
    assert polled.new_items == 1
    assert json.loads(refresh.calls.last.request.content) == {"workspace_id": "ws_1"}

    pending = client.inbox.list_approvals(workspace_id="ws_1")
    assert pending[0].id == 7
    assert pending[0].reply == "Thanks!"
    assert approvals.called

    assert client.inbox.approve_reply(7, text="Edited") == {"id": 7, "outcome": "sent"}
    assert json.loads(approve.calls.last.request.content) == {"text": "Edited"}

    assert client.inbox.unread_count(workspace_id="ws_1") == 4
    assert dict(unread.calls.last.request.url.params) == {"workspace_id": "ws_1"}
