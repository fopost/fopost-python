from __future__ import annotations

from datetime import datetime, timezone

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

SECURITY_EVENT = {
    "id": "evt_1",
    "workspace_id": "ws_1",
    "kind": "security",
    "ref_type": "member_removed",
    "ref_id": "usr_2",
    "summary": "Removed sam@example.com",
    "actor": {"type": "user", "name": "Ada"},
    "time": "2026-09-20T10:00:00Z",
}


@respx.mock
def test_reads_the_audit_log_and_keeps_the_cursor(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/activity").mock(
        return_value=httpx.Response(
            200, json={"data": [SECURITY_EVENT], "meta": {"next_cursor": "42"}}
        )
    )

    page = client.activity.list(
        workspace_id="ws_1",
        kind="security",
        from_=datetime(2026, 9, 1, tzinfo=timezone.utc),
        limit=1,
    )

    params = route.calls[0].request.url.params
    assert params["kind"] == "security"
    assert params["workspace_id"] == "ws_1"
    assert params["from"].startswith("2026-09-01")
    assert len(page) == 1
    assert page[0].ref_type == "member_removed"
    assert page[0].actor.name == "Ada"
    assert page.next_cursor == "42"


@respx.mock
def test_the_end_of_the_list_is_a_null_cursor(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/activity").mock(
        return_value=httpx.Response(200, json={"data": [], "meta": {"next_cursor": None}})
    )

    page = client.activity.list()

    assert list(page) == []
    assert page.next_cursor is None
