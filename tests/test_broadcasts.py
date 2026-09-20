from __future__ import annotations

import json
from typing import Any

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

BROADCAST_FIXTURE: dict[str, Any] = {
    "id": "bc_1",
    "name": "September check-in",
    "text": "New colours just landed.",
    "account_id": "acc_1",
    "audience": {"platforms": ["instagram"]},
    "status": "sent",
    "scheduled_at": None,
    "sent_at": "2026-09-19T10:04:00.000Z",
    "created_at": "2026-09-19T09:58:00.000Z",
    "counts": {"total": 3, "sent": 2, "skipped": 1, "failed": 0, "pending": 0},
}

SEQUENCE_FIXTURE: dict[str, Any] = {
    "id": "seq_1",
    "name": "Welcome",
    "account_id": "acc_1",
    "steps": [
        {"delay_hours": 0, "text": "Thanks for the follow"},
        {"delay_hours": 48, "text": "Here is what people ask first"},
    ],
    "status": "active",
    "created_at": "2026-09-12T08:00:00.000Z",
    "enrollments": {"total": 4, "active": 1, "completed": 3, "stopped": 0, "failed": 0},
}


@respx.mock
def test_list_carries_the_pagination_block(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/broadcasts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [BROADCAST_FIXTURE],
                "pagination": {"page": 2, "per_page": 10, "total": 11},
            },
        )
    )

    page = client.broadcasts.list(workspace_id="ws_1", status="sent", page=2, per_page=10)

    assert len(page) == 1
    assert page[0].name == "September check-in"
    assert page[0].counts is not None and page[0].counts.skipped == 1
    assert page.meta.total == 11
    assert dict(route.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "status": "sent",
        "page": "2",
        "per_page": "10",
    }


@respx.mock
def test_create_sends_the_snake_case_body(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/broadcasts").mock(
        return_value=httpx.Response(201, json={"data": BROADCAST_FIXTURE})
    )

    client.broadcasts.create(
        workspace_id="ws_1",
        account_id="acc_1",
        name="September check-in",
        text="New colours just landed.",
        audience={"platforms": ["instagram"]},
        scheduled_at="2026-10-01T09:00:00.000Z",
    )

    body = json.loads(route.calls.last.request.content)
    assert body["workspace_id"] == "ws_1"
    assert body["account_id"] == "acc_1"
    assert body["scheduled_at"] == "2026-10-01T09:00:00.000Z"


@respx.mock
def test_a_skipped_recipient_keeps_its_reason(client: Fopost) -> None:
    """A closed messaging window has to be readable, or a non-send is a mystery."""
    route = respx.get(f"{BASE_URL}/broadcasts/bc_1/recipients").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "contact_id": "con_1",
                        "display_name": "Sam Rivera",
                        "status": "skipped",
                        "skip_reason": "window_closed",
                        "sent_at": None,
                        "error": None,
                    }
                ],
                "pagination": {"page": 1, "per_page": 50, "total": 1},
            },
        )
    )

    page = client.broadcasts.recipients("bc_1", status="skipped")

    assert page[0].status == "skipped"
    assert page[0].skip_reason == "window_closed"
    assert dict(route.calls.last.request.url.params)["status"] == "skipped"


@respx.mock
def test_send_and_cancel_post_to_their_own_paths(client: Fopost) -> None:
    send = respx.post(f"{BASE_URL}/broadcasts/bc_1/send").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": "bc_1", "status": "sending", "recipients": 3}}
        )
    )
    cancel = respx.post(f"{BASE_URL}/broadcasts/bc_1/cancel").mock(
        return_value=httpx.Response(200, json={"data": {"id": "bc_1", "status": "cancelled"}})
    )

    assert client.broadcasts.send("bc_1")["recipients"] == 3
    assert client.broadcasts.cancel("bc_1")["status"] == "cancelled"
    assert send.called and cancel.called


@respx.mock
def test_sequence_steps_travel_as_given(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/sequences").mock(
        return_value=httpx.Response(201, json={"data": SEQUENCE_FIXTURE})
    )

    sequence = client.sequences.create(
        workspace_id="ws_1",
        account_id="acc_1",
        name="Welcome",
        steps=[{"delay_hours": 0, "text": "Thanks for the follow"}],
    )

    assert sequence.steps[1].delay_hours == 48
    body = json.loads(route.calls.last.request.content)
    assert body["steps"] == [{"delay_hours": 0, "text": "Thanks for the follow"}]


@respx.mock
def test_enroll_takes_ids_or_an_audience(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/sequences/seq_1/enroll").mock(
        return_value=httpx.Response(200, json={"data": {"id": "seq_1", "enrolled": 2}})
    )

    client.sequences.enroll("seq_1", contact_ids=["con_1", "con_2"])
    assert json.loads(route.calls.last.request.content)["contact_ids"] == ["con_1", "con_2"]

    client.sequences.enroll("seq_1", audience={"platforms": ["telegram"]})
    assert json.loads(route.calls.last.request.content)["audience"] == {"platforms": ["telegram"]}


@respx.mock
def test_unenroll_names_the_contacts_it_stops(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/sequences/seq_1/unenroll").mock(
        return_value=httpx.Response(200, json={"data": {"id": "seq_1", "stopped": 1}})
    )

    assert client.sequences.unenroll("seq_1", ["con_1"])["stopped"] == 1
    assert json.loads(route.calls.last.request.content)["contact_ids"] == ["con_1"]
