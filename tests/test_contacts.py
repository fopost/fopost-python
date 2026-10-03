from __future__ import annotations

from typing import Any

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

CONTACT_FIXTURE: dict[str, Any] = {
    "id": "con_1",
    "display_name": "Ada Okafor",
    "channels": [
        {"platform": "instagram", "handle": "adaokafor", "externalId": "178414"},
        {"platform": "x", "handle": "ada_writes", "externalId": None},
    ],
    "source": "inbox",
    "note": None,
    "first_seen_at": "2026-04-02T09:14:00.000Z",
    "last_seen_at": "2026-09-18T14:30:00.000Z",
    "fields": {"plan_tier": "Pro"},
    "labels": [{"id": "lbl_1", "name": "VIP", "color": "#0070f3"}],
}


@respx.mock
def test_list_carries_the_pagination_block(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [CONTACT_FIXTURE],
                "pagination": {"page": 2, "per_page": 10, "total": 11},
            },
        )
    )

    page = client.contacts.list(workspace_id="ws_1", search="ada", page=2, per_page=10)

    assert len(page) == 1
    assert page[0].display_name == "Ada Okafor"
    assert page[0].channels[0].external_id == "178414"
    assert page.meta.total == 11
    assert dict(route.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "search": "ada",
        "page": "2",
        "per_page": "10",
    }


@respx.mock
def test_create_sends_the_wire_names(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(201, json={"data": CONTACT_FIXTURE})
    )

    contact = client.contacts.create(
        workspace_id="ws_1",
        channels=[{"platform": "x", "handle": "ada_writes"}],
        display_name="Ada Okafor",
        fields={"plan_tier": "Pro"},
    )

    assert contact.id == "con_1"
    assert route.calls.last.request.read() == (
        b'{"workspace_id":"ws_1","channels":[{"platform":"x","handle":"ada_writes"}],'
        b'"display_name":"Ada Okafor","fields":{"plan_tier":"Pro"}}'
    )


@respx.mock
def test_update_clears_a_field_with_null_and_omits_what_was_not_passed(client: Fopost) -> None:
    route = respx.patch(f"{BASE_URL}/contacts/con_1").mock(
        return_value=httpx.Response(200, json={"data": CONTACT_FIXTURE})
    )

    client.contacts.update("con_1", fields={"region": None})

    assert route.calls.last.request.read() == b'{"fields":{"region":null}}'


@respx.mock
def test_conversations_returns_the_threads_a_contact_appears_in(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/contacts/con_1/conversations").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "key": "t_182736",
                        "account_id": "acc_1",
                        "account_username": "yourbrand",
                        "platform": "instagram",
                        "messages": 14,
                        "received": 9,
                        "sent": 5,
                        "last_message_at": "2026-09-18T14:30:00.000Z",
                        "last_item_id": "inb_1",
                    }
                ]
            },
        )
    )

    rows = client.contacts.conversations("con_1", limit=10)

    assert len(rows) == 1
    assert rows[0].key == "t_182736"
    assert rows[0].received == 9
    assert dict(route.calls.last.request.url.params) == {"limit": "10"}


@respx.mock
def test_import_reports_what_merged_and_what_was_skipped(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/contacts/import").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "created": 1,
                    "merged": 2,
                    "skipped": [{"row": 4, "reason": "platform and handle are both required"}],
                    "unknownColumns": ["lifetime_value"],
                }
            },
        )
    )

    result = client.contacts.import_csv(workspace_id="ws_1", csv="platform,handle\nx,ada_writes")

    assert result.created == 1
    assert result.merged == 2
    assert result.skipped[0].row == 4
    assert result.unknown_columns == ["lifetime_value"]


@respx.mock
def test_create_field_puts_the_workspace_on_the_query(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/contacts/fields").mock(
        return_value=httpx.Response(
            201,
            json={
                "data": {
                    "id": "fld_1",
                    "key": "plan_tier",
                    "name": "Plan Tier",
                    "type": "select",
                    "options": ["Free", "Pro"],
                    "position": 0,
                }
            },
        )
    )

    field = client.contacts.create_field(
        workspace_id="ws_1",
        key="plan_tier",
        name="Plan Tier",
        type="select",
        options=["Free", "Pro"],
    )

    assert field.key == "plan_tier"
    assert dict(route.calls.last.request.url.params) == {"workspace_id": "ws_1"}


@respx.mock
def test_conversation_analytics_reads_the_analytics_route(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/analytics/inbox/conversations").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "conversations": [
                        {
                            "key": "t_1",
                            "accountId": "acc_1",
                            "platform": "instagram",
                            "received": 9,
                            "sent": 5,
                            "answered": 5,
                            "open": 1,
                            "medianResponseMinutes": 47,
                            "firstMessageAt": None,
                            "lastMessageAt": None,
                        }
                    ],
                    "total": 128,
                    "page": 1,
                    "perPage": 25,
                }
            },
        )
    )

    report = client.contacts.conversation_analytics(days=30, sort="slowest")

    assert report.total == 128
    assert report.conversations[0].median_response_minutes == 47
    assert dict(route.calls.last.request.url.params) == {
        "days": "30",
        "sort": "slowest",
        "page": "1",
        "per_page": "25",
    }
