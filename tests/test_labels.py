from __future__ import annotations

import httpx
import respx

from owlstack import Owlstack
from tests.conftest import BASE_URL, LABEL_FIXTURE


@respx.mock
def test_list_returns_labels_scoped_to_a_workspace(client: Owlstack) -> None:
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
def test_list_without_a_workspace_returns_every_label(client: Owlstack) -> None:
    route = respx.get(f"{BASE_URL}/labels").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    assert client.labels.list() == []
    assert dict(route.calls.last.request.url.params) == {}
