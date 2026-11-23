from __future__ import annotations

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

SCOPE = {"workspace_id": "ws_1", "connection_id": "conn_1", "customer_id": "1234567890"}


@respx.mock
def test_ad_schedule_is_replaced_with_put(client: Fopost) -> None:
    route = respx.put(f"{BASE_URL}/ads/google/ad-schedule").mock(
        return_value=httpx.Response(200, json={"data": {"slots": 2}})
    )
    slots = client.ads.google.set_ad_schedule(
        **SCOPE,
        campaign_id="1234567890~campaign~55",
        slots=[{"dayOfWeek": "MONDAY", "startHour": 9, "endHour": 18}],
    )
    assert slots == 2
    assert route.calls.last.request.method == "PUT"


@respx.mock
def test_query_returns_rows_as_google_sends_them(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/ads/insights/query").mock(
        return_value=httpx.Response(200, json={"data": {"rows": [{"campaign": {"id": "55"}}]}})
    )
    rows = client.ads.google.query(
        connection_id="conn_1",
        customer_id="1234567890",
        query="SELECT campaign.id FROM campaign",
    )
    assert rows == [{"campaign": {"id": "55"}}]


@respx.mock
def test_authorize_google_has_its_own_route(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ads/connections/google/authorize").mock(
        return_value=httpx.Response(200, json={"data": {"url": "https://accounts.google.com/o/x"}})
    )
    url = client.ads.authorize_google(workspace_id="ws_1")
    assert url == "https://accounts.google.com/o/x"
    assert route.called
