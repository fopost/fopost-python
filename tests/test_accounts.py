from __future__ import annotations

from datetime import datetime, timezone

import httpx
import respx

from fopost import Fopost
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
