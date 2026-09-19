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


@respx.mock
def test_create_sends_url_tags(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ads").mock(
        return_value=httpx.Response(201, json={"data": AD_FIXTURE})
    )

    client.ads.create(
        workspace_id="ws_1",
        connection_id="conn_1",
        ad_account_id="act_1",
        page_id="123",
        name="Autumn drop",
        goal="traffic",
        budget=BUDGET,
        targeting=TARGETING,
        text="New in",
        url_tags="utm_source=meta&utm_medium=paid",
    )

    assert json.loads(route.calls.last.request.content)["urlTags"] == (
        "utm_source=meta&utm_medium=paid"
    )


@respx.mock
def test_account_tree_nests_campaigns_ad_sets_and_ads(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/ads/accounts/act_1/tree").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "adAccountId": "act_1",
                    "currency": "USD",
                    "workspaceId": "ws_1",
                    "campaigns": [
                        {
                            "id": "c_1",
                            "name": "Autumn",
                            "status": "PAUSED",
                            "budgetMinor": None,
                            "adSets": [
                                {
                                    "id": "s_1",
                                    "name": "US 21-45",
                                    "status": "ACTIVE",
                                    "campaignId": "c_1",
                                    "budgetMinor": 2000,
                                    "ads": [
                                        {
                                            "id": "a_1",
                                            "name": "Hero",
                                            "status": "ACTIVE",
                                            "adSetId": "s_1",
                                            "creativeId": "cr_1",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            },
        )
    )

    tree = client.ads.account_tree("act_1", connection_id="conn_1", workspace_id="ws_1")

    assert tree.ad_account_id == "act_1"
    ad_set = tree.campaigns[0].ad_sets[0]
    assert ad_set.budget_minor == 2000
    assert ad_set.ads[0].creative_id == "cr_1"
    assert dict(route.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "connection_id": "conn_1",
    }


@respx.mock
def test_campaign_update_is_partial_and_duplicate_returns_the_copy_id(client: Fopost) -> None:
    patch = respx.patch(f"{BASE_URL}/ads/campaigns/c_1").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": "c_1", "name": "Autumn", "status": "ACTIVE"}}
        )
    )
    dup = respx.post(f"{BASE_URL}/ads/campaigns/c_1/duplicate").mock(
        return_value=httpx.Response(201, json={"data": {"id": "c_2"}})
    )
    status = respx.post(f"{BASE_URL}/ads/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": "c_1", "level": "campaign", "ok": True, "error": None},
                    {"id": "a_1", "level": "ad", "ok": False, "error": "Not found"},
                ]
            },
        )
    )

    campaign = client.ads.update_campaign(
        "c_1", workspace_id="ws_1", connection_id="conn_1", status="active"
    )
    assert campaign.status == "ACTIVE"
    assert json.loads(patch.calls.last.request.content) == {"status": "active"}
    assert dict(patch.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "connection_id": "conn_1",
    }

    copy_id = client.ads.duplicate_campaign(
        "c_1", workspace_id="ws_1", connection_id="conn_1", paused=False
    )
    assert copy_id == "c_2"
    assert json.loads(dup.calls.last.request.content) == {"paused": False}

    results = client.ads.bulk_set_status(
        workspace_id="ws_1",
        connection_id="conn_1",
        status="paused",
        objects=[{"id": "c_1", "level": "campaign"}, {"id": "a_1", "level": "ad"}],
    )
    assert [r.ok for r in results] == [True, False]
    assert json.loads(status.calls.last.request.content)["objects"][1] == {
        "id": "a_1",
        "level": "ad",
    }


@respx.mock
def test_insights_send_the_query_params_and_parse_the_report(client: Fopost) -> None:
    report = {
        "objectId": "c_1",
        "currency": "USD",
        "since": "2026-09-01",
        "until": "2026-09-18",
        "breakdownBy": "age",
        "totals": {"impressions": 900, "clicks": 30, "spendMinor": 1200, "ctr": 3.33},
        "breakdown": [{"key": "25-34", "metrics": {"impressions": 400, "clicks": 12}}],
        "timeline": [{"date": "2026-09-01", "metrics": {"impressions": 50}}],
    }
    network = respx.get(f"{BASE_URL}/ads/insights").mock(
        return_value=httpx.Response(200, json={"data": report})
    )
    own = respx.get(f"{BASE_URL}/ads/ad_1/insights").mock(
        return_value=httpx.Response(200, json={"data": report})
    )

    result = client.ads.insights(
        connection_id="conn_1",
        object_id="c_1",
        since="2026-09-01",
        until="2026-09-18",
        breakdown="age",
        daily=True,
    )
    assert result.totals is not None
    assert result.totals.ctr == 3.33
    assert result.breakdown[0].key == "25-34"
    assert result.timeline[0].date == "2026-09-01"
    assert dict(network.calls.last.request.url.params) == {
        "connection_id": "conn_1",
        "object_id": "c_1",
        "since": "2026-09-01",
        "until": "2026-09-18",
        "breakdown": "age",
        "daily": "true",
    }

    client.ads.ad_insights("ad_1", workspace_id="ws_1", since="2026-09-01", until="2026-09-18")
    assert dict(own.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "since": "2026-09-01",
        "until": "2026-09-18",
    }


@respx.mock
def test_leads_feed_follows_the_cursor(client: Fopost) -> None:
    lead = {
        "id": "7c1e0b5a-0000-4000-8000-000000000001",
        "leadId": "m_1",
        "connectionId": "conn_1",
        "pageId": "123",
        "formId": "form_1",
        "isOrganic": False,
        "fields": [{"name": "email", "values": ["a@yourbrand.com"]}],
        "submittedAt": "2026-09-18T15:00:00.000Z",
    }
    route = respx.get(f"{BASE_URL}/ads/leads").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"leads": [lead], "nextCursor": "cur_2"}}),
            httpx.Response(200, json={"data": {"leads": [], "nextCursor": None}}),
        ]
    )

    first = client.ads.leads_feed(workspace_id="ws_1", form_id="form_1", limit=50)
    assert first.leads[0].lead_id == "m_1"
    assert first.next_cursor == "cur_2"
    assert dict(route.calls[0].request.url.params) == {
        "workspace_id": "ws_1",
        "form_id": "form_1",
        "limit": "50",
    }

    second = client.ads.leads_feed(workspace_id="ws_1", cursor=first.next_cursor)
    assert second.next_cursor is None
    assert dict(route.calls[1].request.url.params) == {"workspace_id": "ws_1", "cursor": "cur_2"}


@respx.mock
def test_lead_pages_and_audience_users(client: Fopost) -> None:
    subscribe = respx.post(f"{BASE_URL}/ads/lead-pages").mock(
        return_value=httpx.Response(201, json={"data": {"pageId": "123", "backfilled": 4}})
    )
    unsubscribe = respx.delete(f"{BASE_URL}/ads/lead-pages/123").mock(
        return_value=httpx.Response(200, json={"message": "Unsubscribed"})
    )
    users = respx.post(f"{BASE_URL}/ads/audiences/aud_1/users").mock(
        return_value=httpx.Response(200, json={"data": {"added": 2}})
    )

    sub = client.ads.subscribe_lead_page(workspace_id="ws_1", connection_id="conn_1", page_id="123")
    assert sub.backfilled == 4
    assert json.loads(subscribe.calls.last.request.content) == {
        "workspaceId": "ws_1",
        "connectionId": "conn_1",
        "pageId": "123",
    }

    client.ads.unsubscribe_lead_page("123", workspace_id="ws_1", connection_id="conn_1")
    assert dict(unsubscribe.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "connection_id": "conn_1",
    }

    added = client.ads.add_audience_users(
        "aud_1",
        workspace_id="ws_1",
        connection_id="conn_1",
        emails=["a@yourbrand.com", "b@yourbrand.com"],
    )
    assert added == 2
    assert json.loads(users.calls.last.request.content) == {
        "emails": ["a@yourbrand.com", "b@yourbrand.com"]
    }
