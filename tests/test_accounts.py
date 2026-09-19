from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
import respx

from fopost import Fopost, FopostError
from tests.conftest import ACCOUNT_FIXTURE, BASE_URL


@respx.mock
def test_list_parses_camel_case_and_sends_the_camel_query_param(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts").mock(
        return_value=httpx.Response(200, json={"data": [ACCOUNT_FIXTURE]})
    )

    accounts = client.accounts.list(workspace_id="ws_1")

    assert len(accounts) == 1
    assert accounts[0].id == "acc_1"
    assert accounts[0].workspace_id == "ws_1"
    assert accounts[0].is_primary is True
    assert accounts[0].health_status == "healthy"
    assert accounts[0].last_health_check == datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc)

    # The accounts endpoint reads workspaceId, unlike posts and labels.
    assert dict(route.calls.last.request.url.params) == {"workspaceId": "ws_1"}


@respx.mock
def test_list_without_a_workspace_sends_no_params(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    assert client.accounts.list() == []
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
def test_get_returns_one_account(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1").mock(
        return_value=httpx.Response(200, json={"data": ACCOUNT_FIXTURE})
    )

    account = client.accounts.get("acc_1")

    assert account.platform == "twitter"
    assert account.username == "fopost"


@respx.mock
def test_health_returns_the_raw_payload(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/health").mock(
        return_value=httpx.Response(200, json={"data": {"status": "healthy", "checks": []}})
    )

    assert client.accounts.health("acc_1") == {"status": "healthy", "checks": []}


@respx.mock
def test_list_filters_by_group(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts").mock(
        return_value=httpx.Response(
            200, json={"data": [{**ACCOUNT_FIXTURE, "platformName": "FoPost HQ"}]}
        )
    )

    accounts = client.accounts.list(group_id="grp_1")

    assert accounts[0].platform_name == "FoPost HQ"
    assert dict(route.calls.last.request.url.params) == {"group_id": "grp_1"}


@respx.mock
def test_update_sends_the_display_name_and_null_resets_it(client: Fopost) -> None:
    route = respx.patch(f"{BASE_URL}/accounts/acc_1").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": "acc_1", "name": "Brand", "platform_name": "FoPost"}}
        )
    )

    renamed = client.accounts.update("acc_1", display_name="Brand")
    assert renamed.name == "Brand"
    assert renamed.platform_name == "FoPost"
    assert json.loads(route.calls.last.request.content) == {"display_name": "Brand"}

    client.accounts.update("acc_1", display_name=None)
    assert json.loads(route.calls.last.request.content) == {"display_name": None}


@respx.mock
def test_move_posts_the_target_workspace(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/accounts/acc_1/move").mock(
        return_value=httpx.Response(200, json={"data": {"id": "acc_1", "workspace_id": "ws_2"}})
    )

    moved = client.accounts.move("acc_1", workspace_id="ws_2")

    assert moved.workspace_id == "ws_2"
    assert json.loads(route.calls.last.request.content) == {"workspace_id": "ws_2"}


@respx.mock
def test_move_conflict_keeps_the_blocking_tables_on_the_error(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/accounts/acc_1/move").mock(
        return_value=httpx.Response(
            409,
            json={
                "error": "move_blocked",
                "message": "Account has history",
                "blocking_tables": ["posts"],
            },
        )
    )

    with pytest.raises(FopostError) as caught:
        client.accounts.move("acc_1", workspace_id="ws_2")

    assert caught.value.status == 409
    assert caught.value.code == "move_blocked"
    assert caught.value.body["blocking_tables"] == ["posts"]
