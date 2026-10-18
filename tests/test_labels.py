from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL, LABEL_FIXTURE


@respx.mock
def test_list_returns_labels_scoped_to_a_workspace(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/labels").mock(
        return_value=httpx.Response(200, json={"data": [LABEL_FIXTURE]})
    )

    labels = client.labels.list(workspace_id="ws_1")

    assert len(labels) == 1
    assert labels[0].id == "lbl_1"
    assert labels[0].name == "Launch"
    assert labels[0].workspace is not None
    assert labels[0].workspace["slug"] == "acme"
    assert dict(route.calls.last.request.url.params) == {"workspace_id": "ws_1"}


@respx.mock
def test_list_without_a_workspace_returns_every_label(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/labels").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    assert client.labels.list() == []
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
def test_create_get_update_and_delete(client: Fopost) -> None:
    created = respx.post(f"{BASE_URL}/labels").mock(
        return_value=httpx.Response(201, json=LABEL_FIXTURE)
    )
    respx.get(f"{BASE_URL}/labels/lbl_1").mock(
        return_value=httpx.Response(200, json={"data": LABEL_FIXTURE})
    )
    updated = respx.put(f"{BASE_URL}/labels/lbl_1").mock(
        return_value=httpx.Response(200, json={**LABEL_FIXTURE, "name": "Renamed"})
    )
    deleted = respx.delete(f"{BASE_URL}/labels/lbl_1").mock(return_value=httpx.Response(204))

    label = client.labels.create(workspace_id="ws_1", name="Launch", color="#4F46E5")
    assert label.id == "lbl_1"
    assert json.loads(created.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "name": "Launch",
        "color": "#4F46E5",
    }

    assert client.labels.get("lbl_1").name == "Launch"

    assert client.labels.update("lbl_1", name="Renamed", color="#000000").name == "Renamed"
    assert json.loads(updated.calls.last.request.content) == {
        "name": "Renamed",
        "color": "#000000",
    }

    client.labels.delete("lbl_1")
    assert deleted.called
