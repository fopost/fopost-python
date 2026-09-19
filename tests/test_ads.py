from __future__ import annotations

import json

import httpx
import respx

from fopost import Ad, Fopost
from tests.conftest import BASE_URL

AD_FIXTURE = {
    "id": "ad_1",
    "workspaceId": "ws_1",
    "kind": "boost",
    "name": "Autumn drop boost",
    "goal": "engagement",
    "status": "paused",
    "effectiveStatus": "PAUSED",
    "connectionId": "conn_1",
    "adAccountId": "act_1",
    "budgetMinor": 2000,
    "budgetType": "daily",
    "currency": "USD",
    "targeting": {"countries": ["US"], "ageMin": 21, "ageMax": 45, "gender": "all"},
    "insights": {"impressions": 120, "reach": 100, "clicks": 4, "spendMinor": 350},
    "createdAt": "2026-09-18T15:00:00.000Z",
}

BUDGET = {"minor": 2000, "type": "daily"}
TARGETING = {"countries": ["US"], "ageMin": 21, "ageMax": 45, "gender": "all"}


@respx.mock
def test_boost_sends_the_camel_case_body_and_parses_the_ad(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ads/boost").mock(
        return_value=httpx.Response(201, json={"data": AD_FIXTURE})
    )

    ad = client.ads.boost(
        workspace_id="ws_1",
        connection_id="conn_1",
        ad_account_id="act_1",
        post_id="post_1",
        account_id="acc_1",
        name="Autumn drop boost",
        goal="engagement",
        budget=BUDGET,
        targeting=TARGETING,
    )

    assert isinstance(ad, Ad)
    assert ad.id == "ad_1"
    assert ad.budget_minor == 2000
    assert ad.insights is not None
    assert ad.insights.spend_minor == 350
    assert json.loads(route.calls.last.request.content) == {
        "workspaceId": "ws_1",
        "connectionId": "conn_1",
        "adAccountId": "act_1",
        "postId": "post_1",
        "accountId": "acc_1",
        "name": "Autumn drop boost",
        "goal": "engagement",
        "budget": BUDGET,
        "targeting": TARGETING,
    }
    assert route.calls.last.request.headers["x-api-key"] == "osk_test_key"


@respx.mock
def test_status_refresh_and_delete_address_one_ad_by_workspace(client: Fopost) -> None:
    patch = respx.patch(f"{BASE_URL}/ads/ad_1").mock(
        return_value=httpx.Response(200, json={"data": {**AD_FIXTURE, "status": "active"}})
    )
    refresh = respx.post(f"{BASE_URL}/ads/ad_1/refresh").mock(
        return_value=httpx.Response(200, json={"data": AD_FIXTURE})
    )
    delete = respx.delete(f"{BASE_URL}/ads/ad_1").mock(
        return_value=httpx.Response(200, json={"message": "Ad deleted"})
    )

    assert client.ads.set_status("ad_1", workspace_id="ws_1", status="active").status == "active"
    assert dict(patch.calls.last.request.url.params) == {"workspace_id": "ws_1"}
    assert json.loads(patch.calls.last.request.content) == {"status": "active"}

    assert client.ads.refresh("ad_1", workspace_id="ws_1").id == "ad_1"
    assert dict(refresh.calls.last.request.url.params) == {"workspace_id": "ws_1"}

    client.ads.delete("ad_1", workspace_id="ws_1")
    assert dict(delete.calls.last.request.url.params) == {"workspace_id": "ws_1"}


@respx.mock
def test_reads_send_snake_case_query_params(client: Fopost) -> None:
    ads = respx.get(f"{BASE_URL}/ads").mock(
        return_value=httpx.Response(200, json={"data": [AD_FIXTURE]})
    )
    audiences = respx.get(f"{BASE_URL}/ads/audiences").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "audiences": [{"id": "aud_1", "name": "Buyers", "subtype": "CUSTOM"}],
                    "pixels": [{"id": "px_1", "name": "Site"}],
                    "workspaceId": "ws_1",
                }
            },
        )
    )
    search = respx.get(f"{BASE_URL}/ads/targeting/search").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "2420", "name": "Berlin", "detail": "Germany"}]}
        )
    )
    leads = respx.get(f"{BASE_URL}/ads/lead-forms/form_1/leads").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "leads": [
                        {
                            "id": "l_1",
                            "fields": [{"name": "email", "values": ["a@yourbrand.com"]}],
                            "isOrganic": False,
                        }
                    ],
                    "nextCursor": "cur_2",
                }
            },
        )
    )

    assert client.ads.list(workspace_id="ws_1")[0].id == "ad_1"
    assert dict(ads.calls.last.request.url.params) == {"workspace_id": "ws_1"}

    result = client.ads.audiences(connection_id="conn_1", ad_account_id="act_1")
    assert result.audiences[0].name == "Buyers"
    assert result.pixels[0]["id"] == "px_1"
    assert dict(audiences.calls.last.request.url.params) == {
        "connection_id": "conn_1",
        "ad_account_id": "act_1",
    }

    options = client.ads.search_targeting(connection_id="conn_1", type="city", q="Berlin")
    assert options[0].name == "Berlin"
    assert dict(search.calls.last.request.url.params) == {
        "connection_id": "conn_1",
        "type": "city",
        "q": "Berlin",
    }

    page = client.ads.leads("form_1", connection_id="conn_1", page_id="123", after="cur_1")
    assert page.leads[0].fields[0]["values"] == ["a@yourbrand.com"]
    assert page.next_cursor == "cur_2"
    assert dict(leads.calls.last.request.url.params) == {
        "connection_id": "conn_1",
        "page_id": "123",
        "after": "cur_1",
    }
