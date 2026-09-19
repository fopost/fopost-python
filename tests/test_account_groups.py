from __future__ import annotations

import json
from typing import Any

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

GROUP_FIXTURE: dict[str, Any] = {
    "id": "grp_1",
    "name": "Launch",
    "account_ids": ["acc_1", "acc_2"],
    "created_at": "2026-09-01T10:00:00.000Z",
    "updated_at": "2026-09-01T10:00:00.000Z",
}


@respx.mock
def test_list_is_scoped_to_a_workspace(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/account-groups").mock(
        return_value=httpx.Response(200, json={"data": [GROUP_FIXTURE]})
    )

    groups = client.account_groups.list(workspace_id="ws_1")

    assert [g.id for g in groups] == ["grp_1"]
    assert groups[0].account_ids == ["acc_1", "acc_2"]
    assert dict(route.calls.last.request.url.params) == {"workspace_id": "ws_1"}


@respx.mock
def test_create_sends_workspace_name_and_members(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/account-groups").mock(
        return_value=httpx.Response(201, json={"data": GROUP_FIXTURE})
    )

    group = client.account_groups.create(
        workspace_id="ws_1", name="Launch", account_ids=["acc_1", "acc_2"]
    )

    assert group.name == "Launch"
    assert json.loads(route.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "name": "Launch",
        "account_ids": ["acc_1", "acc_2"],
    }


@respx.mock
def test_create_without_members_omits_account_ids(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/account-groups").mock(
        return_value=httpx.Response(201, json={"data": GROUP_FIXTURE})
    )

    client.account_groups.create(workspace_id="ws_1", name="Launch")

    assert json.loads(route.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "name": "Launch",
    }


@respx.mock
def test_get_update_delete_and_set_members(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/account-groups/grp_1").mock(
        return_value=httpx.Response(200, json={"data": GROUP_FIXTURE})
    )
    patch = respx.patch(f"{BASE_URL}/account-groups/grp_1").mock(
        return_value=httpx.Response(200, json={"data": {**GROUP_FIXTURE, "name": "Renamed"}})
    )
    delete = respx.delete(f"{BASE_URL}/account-groups/grp_1").mock(
        return_value=httpx.Response(200, json={"message": "Account group deleted"})
    )
    members = respx.put(f"{BASE_URL}/account-groups/grp_1/members").mock(
        return_value=httpx.Response(200, json={"data": {**GROUP_FIXTURE, "account_ids": ["acc_3"]}})
    )

    assert client.account_groups.get("grp_1").id == "grp_1"
    assert client.account_groups.update("grp_1", name="Renamed").name == "Renamed"
    assert json.loads(patch.calls.last.request.content) == {"name": "Renamed"}
    assert client.account_groups.set_members("grp_1", ["acc_3"]).account_ids == ["acc_3"]
    assert json.loads(members.calls.last.request.content) == {"account_ids": ["acc_3"]}
    client.account_groups.delete("grp_1")
    assert delete.called
