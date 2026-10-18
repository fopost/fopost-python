from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL, WORKSPACE_FIXTURE


@respx.mock
def test_list_parses_the_mixed_casing_the_api_returns(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/workspaces").mock(
        return_value=httpx.Response(200, json={"data": [WORKSPACE_FIXTURE]})
    )

    workspaces = client.workspaces.list()

    assert len(workspaces) == 1
    ws = workspaces[0]
    assert ws.id == "ws_1"
    assert ws.require_approval is False
    assert ws.ai_alt_text_enabled is True
    assert ws.brand_color == "#4F46E5"
    assert ws.role == "owner"
    assert ws.created_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    # Nested accounts come back camelCase even though the workspace is snake.
    assert ws.accounts[0].workspace_id == "ws_1"
    assert route.called


@respx.mock
def test_get_returns_one_workspace(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/workspaces/ws_1").mock(
        return_value=httpx.Response(200, json={"data": WORKSPACE_FIXTURE})
    )

    assert client.workspaces.get("ws_1").name == "Acme"


@respx.mock
def test_create_update_and_delete(client: Fopost) -> None:
    created = respx.post(f"{BASE_URL}/workspaces").mock(
        return_value=httpx.Response(201, json=WORKSPACE_FIXTURE)
    )
    updated = respx.put(f"{BASE_URL}/workspaces/ws_1").mock(
        return_value=httpx.Response(
            200,
            json={
                **WORKSPACE_FIXTURE,
                "name": "Acme Co",
                "connect_redirect_domains": ["yourbrand.com"],
            },
        )
    )
    deleted = respx.delete(f"{BASE_URL}/workspaces/ws_1").mock(return_value=httpx.Response(204))

    ws = client.workspaces.create(name="Acme", type="BRAND", timezone="UTC")
    assert ws.id == "ws_1"
    assert json.loads(created.calls.last.request.content) == {
        "name": "Acme",
        "type": "BRAND",
        "timezone": "UTC",
    }

    changed = client.workspaces.update(
        "ws_1", name="Acme Co", require_approval=True, connect_redirect_domains=["yourbrand.com"]
    )
    assert changed.name == "Acme Co"
    assert changed.connect_redirect_domains == ["yourbrand.com"]
    assert json.loads(updated.calls.last.request.content) == {
        "name": "Acme Co",
        "requireApproval": True,
        "connectRedirectDomains": ["yourbrand.com"],
    }

    client.workspaces.delete("ws_1")
    assert deleted.called
