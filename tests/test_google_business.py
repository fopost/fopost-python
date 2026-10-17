from __future__ import annotations

import json

import httpx
import pytest
import respx

from fopost import Fopost, FopostError
from tests.conftest import BASE_URL


@respx.mock
def test_every_method_maps_onto_its_route_and_body(client: Fopost) -> None:
    routes = [
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/location"),
        respx.patch(f"{BASE_URL}/accounts/acc_1/gbp/location"),
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/attributes"),
        respx.patch(f"{BASE_URL}/accounts/acc_1/gbp/attributes"),
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/menus"),
        respx.put(f"{BASE_URL}/accounts/acc_1/gbp/menus"),
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/services"),
        respx.put(f"{BASE_URL}/accounts/acc_1/gbp/services"),
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/media"),
        respx.post(f"{BASE_URL}/accounts/acc_1/gbp/media"),
        respx.delete(f"{BASE_URL}/accounts/acc_1/gbp/media/CAoSL"),
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/place-actions"),
        respx.post(f"{BASE_URL}/accounts/acc_1/gbp/place-actions"),
        respx.patch(f"{BASE_URL}/accounts/acc_1/gbp/place-actions/links-1"),
        respx.delete(f"{BASE_URL}/accounts/acc_1/gbp/place-actions/links-1"),
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/verification"),
        respx.post(f"{BASE_URL}/accounts/acc_1/gbp/verification/start"),
        respx.post(f"{BASE_URL}/accounts/acc_1/gbp/verification/complete"),
        respx.get(f"{BASE_URL}/accounts/acc_1/gbp/performance"),
    ]
    for route in routes:
        route.mock(return_value=httpx.Response(200, json={"data": {"ok": True}}))

    gb = client.google_business
    assert gb.get_location("acc_1") == {"ok": True}
    gb.update_location("acc_1", title="Corner Bakery", primary_phone="+15550100")
    gb.get_attributes("acc_1", available=True, region_code="US")
    gb.update_attributes("acc_1", [{"name": "attributes/has_wifi", "values": [True]}])
    gb.get_menus("acc_1")
    gb.replace_menus("acc_1", [])
    gb.get_services("acc_1")
    gb.replace_services("acc_1", [])
    gb.list_media("acc_1")
    gb.add_media("acc_1", media_id="m1", category="INTERIOR")
    gb.delete_media("acc_1", "CAoSL")
    gb.list_place_actions("acc_1")
    gb.create_place_action("acc_1", uri="https://example.com/book", place_action_type="APPOINTMENT")
    gb.update_place_action("acc_1", "links-1", is_preferred=True)
    gb.delete_place_action("acc_1", "links-1")
    gb.get_verification_options("acc_1")
    gb.start_verification("acc_1", method="SMS", phone_number="+15550100")
    gb.complete_verification("acc_1", verification_name="v1", pin="123456")
    gb.get_performance(
        "acc_1",
        start_date="2026-09-01",
        end_date="2026-09-07",
        daily_metrics=["CALL_CLICKS", "WEBSITE_CLICKS"],
    )

    for route in routes:
        assert route.called

    # A patch carries only what the caller set.
    patch_location = json.loads(routes[1].calls.last.request.content)
    assert patch_location == {"title": "Corner Bakery", "primary_phone": "+15550100"}
    assert json.loads(routes[13].calls.last.request.content) == {"is_preferred": True}

    # The photo comes from the library, by id.
    assert json.loads(routes[9].calls.last.request.content) == {
        "media_id": "m1",
        "category": "INTERIOR",
    }


@respx.mock
def test_performance_repeats_the_metric_parameter(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts/acc_1/gbp/performance").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )

    client.google_business.get_performance(
        "acc_1",
        start_date="2026-09-01",
        end_date="2026-09-07",
        daily_metrics=["CALL_CLICKS", "WEBSITE_CLICKS"],
    )

    params = route.calls.last.request.url.params
    assert params.get_list("daily_metrics") == ["CALL_CLICKS", "WEBSITE_CLICKS"]
    assert params["start_date"] == "2026-09-01"


@respx.mock
def test_search_keywords_asks_the_same_route_for_the_monthly_terms(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts/acc_1/gbp/performance").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )

    client.google_business.get_search_keywords(
        "acc_1", start_date="2026-08-01", end_date="2026-09-01"
    )

    assert route.calls.last.request.url.params["keywords"] == "true"


@respx.mock
def test_a_pending_api_grant_raises_a_503(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/gbp/location").mock(
        return_value=httpx.Response(
            503, json={"error": "configuration_error", "message": "Not available yet"}
        )
    )

    with pytest.raises(FopostError) as excinfo:
        client.google_business.get_location("acc_1")

    assert excinfo.value.status == 503
    assert excinfo.value.code == "configuration_error"
