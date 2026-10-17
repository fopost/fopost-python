from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost

from .conftest import BASE_URL


@respx.mock
def test_ice_breakers_round_trip(client: Fopost) -> None:
    path = f"{BASE_URL}/accounts/acc_1/messaging/ice-breakers"
    ice_breakers = [{"question": "What are your hours?", "payload": "HOURS"}]
    respx.get(path).mock(
        return_value=httpx.Response(200, json={"data": {"ice_breakers": ice_breakers}})
    )
    put = respx.put(path).mock(
        return_value=httpx.Response(200, json={"data": {"ice_breakers": ice_breakers}})
    )
    respx.delete(path).mock(return_value=httpx.Response(200, json={"data": {"ice_breakers": []}}))

    assert client.accounts.get_ice_breakers("acc_1").ice_breakers[0].payload == "HOURS"

    result = client.accounts.set_ice_breakers("acc_1", ice_breakers)
    assert result.ice_breakers[0].question == "What are your hours?"
    assert json.loads(put.calls.last.request.content) == {"ice_breakers": ice_breakers}

    assert client.accounts.delete_ice_breakers("acc_1").ice_breakers == []


@respx.mock
def test_persistent_menu_and_greeting(client: Fopost) -> None:
    menu_path = f"{BASE_URL}/accounts/acc_1/messaging/persistent-menu"
    menu = [
        {
            "locale": "default",
            "call_to_actions": [
                {"type": "postback", "title": "Talk to Us", "payload": "HUMAN"},
                {"type": "web_url", "title": "Shop", "url": "https://example.com/shop"},
            ],
        }
    ]
    respx.get(menu_path).mock(
        return_value=httpx.Response(200, json={"data": {"persistent_menu": menu}})
    )
    put_menu = respx.put(menu_path).mock(
        return_value=httpx.Response(200, json={"data": {"persistent_menu": menu}})
    )

    read = client.accounts.get_persistent_menu("acc_1")
    assert read.persistent_menu[0].call_to_actions[1].url == "https://example.com/shop"
    client.accounts.set_persistent_menu("acc_1", menu)
    assert json.loads(put_menu.calls.last.request.content) == {"persistent_menu": menu}

    greeting_path = f"{BASE_URL}/accounts/acc_1/messaging/greeting"
    greeting = [{"locale": "default", "text": "Hi! Ask us anything."}]
    put_greeting = respx.put(greeting_path).mock(
        return_value=httpx.Response(200, json={"data": {"greeting": greeting}})
    )
    respx.delete(greeting_path).mock(
        return_value=httpx.Response(200, json={"data": {"greeting": []}})
    )

    client.accounts.set_greeting("acc_1", greeting)
    assert json.loads(put_greeting.calls.last.request.content) == {"greeting": greeting}
    assert client.accounts.delete_greeting("acc_1").greeting == []


@respx.mock
def test_webhook_subscription_reports_and_resubscribes(client: Fopost) -> None:
    path = f"{BASE_URL}/accounts/acc_1/webhook-subscription"
    respx.get(path).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"subscribed": False, "fields": ["feed"], "missing_fields": ["messages"]}
            },
        )
    )
    respx.post(path).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "subscribed": True,
                    "fields": ["feed", "messages"],
                    "missing_fields": [],
                }
            },
        )
    )

    lapsed = client.accounts.get_webhook_subscription("acc_1")
    assert lapsed.subscribed is False
    assert lapsed.missing_fields == ["messages"]

    fixed = client.accounts.resubscribe_webhook("acc_1")
    assert fixed.subscribed is True


@respx.mock
def test_handover_passes_and_takes_control(client: Fopost) -> None:
    path = f"{BASE_URL}/inbox/conversations/t_1/handover"
    route = respx.post(path).mock(
        return_value=httpx.Response(
            200, json={"data": {"app_id": "263902037430900", "control": "passed"}}
        )
    )

    passed = client.inbox.handover("t_1", account_id="acc_1", app_id="263902037430900")
    assert passed.control == "passed"
    assert json.loads(route.calls.last.request.content) == {
        "account_id": "acc_1",
        "app_id": "263902037430900",
    }

    client.inbox.handover("t_1", account_id="acc_1")
    assert json.loads(route.calls.last.request.content) == {"account_id": "acc_1"}
