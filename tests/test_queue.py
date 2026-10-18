from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

SLOT = {
    "id": "slot_1",
    "workspace_id": "ws_1",
    "account_id": None,
    "weekday": 1,
    "time": "09:00",
    "timezone": "Europe/Zagreb",
    "created_at": "2026-10-01T00:00:00.000Z",
}


@respx.mock
def test_slots_crud_sends_bodies_and_reads_moved_posts(client: Fopost) -> None:
    listed = respx.get(f"{BASE_URL}/queue/slots").mock(
        return_value=httpx.Response(200, json={"data": [SLOT]})
    )
    created = respx.post(f"{BASE_URL}/queue/slots").mock(
        return_value=httpx.Response(201, json=SLOT)
    )
    updated = respx.put(f"{BASE_URL}/queue/slots/slot_1").mock(
        return_value=httpx.Response(
            200,
            json={
                **SLOT,
                "time": "10:00",
                "moved": [
                    {
                        "id": "post_1",
                        "from": "2026-10-05T09:00:00.000Z",
                        "to": "2026-10-05T10:00:00.000Z",
                    }
                ],
            },
        )
    )
    deleted = respx.delete(f"{BASE_URL}/queue/slots/slot_1").mock(
        return_value=httpx.Response(200, json={"deleted": True, "moved": []})
    )

    slots = client.queue.list_slots(workspace_id="ws_1")
    assert [s.id for s in slots] == ["slot_1"]
    assert dict(listed.calls.last.request.url.params) == {"workspace_id": "ws_1"}

    slot = client.queue.create_slot(
        workspace_id="ws_1", weekday=1, time="09:00", timezone="Europe/Zagreb"
    )
    assert slot.weekday == 1 and slot.account_id is None
    assert json.loads(created.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "weekday": 1,
        "time": "09:00",
        "timezone": "Europe/Zagreb",
    }

    change = client.queue.update_slot("slot_1", time="10:00")
    assert json.loads(updated.calls.last.request.content) == {"time": "10:00"}
    assert change.time == "10:00"
    assert change.moved[0].from_ == "2026-10-05T09:00:00.000Z"
    assert change.moved[0].to == "2026-10-05T10:00:00.000Z"

    gone = client.queue.delete_slot("slot_1")
    assert deleted.called and gone.deleted is True and gone.moved == []


@respx.mock
def test_next_and_preview_decode_times(client: Fopost) -> None:
    nxt = respx.get(f"{BASE_URL}/queue/next").mock(
        return_value=httpx.Response(200, json={"next": "2026-10-05T09:00:00.000Z"})
    )
    preview = respx.get(f"{BASE_URL}/queue/preview").mock(
        return_value=httpx.Response(
            200, json={"data": ["2026-10-05T09:00:00.000Z", "2026-10-06T09:00:00.000Z"]}
        )
    )

    assert client.queue.next(workspace_id="ws_1", account_id="acc_1") == datetime(
        2026, 10, 5, 9, tzinfo=timezone.utc
    )
    assert dict(nxt.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "account_id": "acc_1",
    }

    times = client.queue.preview(workspace_id="ws_1", count=2)
    assert times == [
        datetime(2026, 10, 5, 9, tzinfo=timezone.utc),
        datetime(2026, 10, 6, 9, tzinfo=timezone.utc),
    ]
    assert dict(preview.calls.last.request.url.params) == {"workspace_id": "ws_1", "count": "2"}
