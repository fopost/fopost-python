from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

SCOPE = {"workspace_id": "ws_1", "connection_id": "conn_1", "customer_id": "1234567890"}

KEYWORD_FIXTURE = {
    "id": "1234567890~keyword~77~99",
    "adGroupId": "1234567890~adGroup~77",
    "text": "running shoes",
    "matchType": "EXACT",
    "status": "ENABLED",
    "cpcBidMinor": 180,
    "negative": False,
}


@respx.mock
def test_keywords_name_the_connection_and_the_customer(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/ads/google/keywords").mock(
        return_value=httpx.Response(200, json={"data": [KEYWORD_FIXTURE]})
    )
    keywords = client.ads.google.keywords(
        connection_id="conn_1", customer_id="1234567890", ad_group_id="1234567890~adGroup~77"
    )
    assert keywords[0].cpc_bid_minor == 180
    assert keywords[0].match_type == "EXACT"
    params = route.calls.last.request.url.params
    assert params["connection_id"] == "conn_1"
    assert params["customer_id"] == "1234567890"
    assert params["ad_group_id"] == "1234567890~adGroup~77"


@respx.mock
def test_create_keyword_sends_the_camel_case_body(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ads/google/keywords").mock(
        return_value=httpx.Response(201, json={"data": {"id": "1234567890~keyword~77~99"}})
    )
    created = client.ads.google.create_keyword(
        **SCOPE, ad_group_id="1234567890~adGroup~77", text="running shoes", match_type="EXACT"
    )
    assert created == "1234567890~keyword~77~99"
    body = json.loads(route.calls.last.request.content)
    assert body["adGroupId"] == "1234567890~adGroup~77"
    assert body["matchType"] == "EXACT"
    assert body["customerId"] == "1234567890"


@respx.mock
def test_delete_carries_the_scope_in_the_body(client: Fopost) -> None:
    route = respx.delete(f"{BASE_URL}/ads/google/assets/1234567890~asset~4321").mock(
        return_value=httpx.Response(204)
    )
    client.ads.google.delete_asset("1234567890~asset~4321", **SCOPE)
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "workspaceId": "ws_1",
        "connectionId": "conn_1",
        "customerId": "1234567890",
    }


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
