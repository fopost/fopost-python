from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

SCOPE = {"workspace_id": "ws_1", "connection_id": "conn_1", "ad_account_id": "act_1"}


@respx.mock
def test_send_conversions_carries_the_idempotency_key_and_reports_a_replay(
    client: Fopost,
) -> None:
    route = respx.post(f"{BASE_URL}/ads/conversions/events").mock(
        return_value=httpx.Response(
            202,
            json={"data": {"id": "cb_1", "accepted": 0, "eventCount": 1, "replayed": True}},
            headers={"Idempotency-Replayed": "true"},
        )
    )

    result = client.ads.send_conversions(
        pixel_id="px_1",
        events=[
            {
                "eventName": "Purchase",
                "occurredAt": "2026-10-18T10:04:00Z",
                "eventId": "order-42",
                "actionSource": "website",
                "email": "someone@example.com",
                "valueMinor": 1999,
                "currency": "USD",
            }
        ],
        idempotency_key="order-42",
        **SCOPE,
    )

    assert result.replayed is True
    assert result.event_count == 1
    request = route.calls.last.request
    assert request.headers["idempotency-key"] == "order-42"
    assert request.headers["x-api-key"] == "osk_test_key"
    body = json.loads(request.content)
    assert body["pixelId"] == "px_1"
    assert body["events"][0]["eventId"] == "order-42"


@respx.mock
def test_pixel_detail_reads_the_install_code(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/ads/pixels/px_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "id": "px_1",
                    "name": "Site",
                    "code": "<script>...</script>",
                    "createdAt": "2026-10-01T00:00:00Z",
                    "lastFiredAt": None,
                    "isUnavailable": False,
                    "dataUseSetting": "advertising_and_analytics",
                }
            },
        )
    )

    pixel = client.ads.get_pixel("px_1", **SCOPE)

    assert pixel.code == "<script>...</script>"
    assert pixel.data_use_setting == "advertising_and_analytics"
    assert pixel.is_unavailable is False
    params = route.calls.last.request.url.params
    assert params["connection_id"] == "conn_1"
    assert params["ad_account_id"] == "act_1"


@respx.mock
def test_create_custom_conversion_sends_the_rule_and_parses_it_back(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ads/custom-conversions").mock(
        return_value=httpx.Response(
            201,
            json={
                "data": {
                    "id": "cc_1",
                    "name": "Checkout",
                    "pixelId": "px_1",
                    "eventType": "PURCHASE",
                    "rule": {"eventName": "PageView", "urlContains": "/thank-you"},
                    "description": None,
                    "defaultValueMinor": 1999,
                    "isArchived": False,
                    "isUnavailable": False,
                    "createdAt": None,
                    "lastFiredAt": None,
                }
            },
        )
    )

    conversion = client.ads.create_custom_conversion(
        pixel_id="px_1",
        name="Checkout",
        event_type="PURCHASE",
        rule={"eventName": "PageView", "urlContains": "/thank-you"},
        default_value_minor=1999,
        **SCOPE,
    )

    assert conversion.id == "cc_1"
    assert conversion.rule is not None
    assert conversion.rule.url_contains == "/thank-you"
    body = json.loads(route.calls.last.request.content)
    assert body["eventType"] == "PURCHASE"
    assert body["rule"] == {"eventName": "PageView", "urlContains": "/thank-you"}
    assert body["defaultValueMinor"] == 1999
    assert "description" not in body
