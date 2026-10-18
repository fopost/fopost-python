from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

SESSION = {
    "id": "cs_1",
    "status": "pending",
    "external_user_id": "user-42",
    "platforms": ["twitter", "linkedin"],
    "redirect_url": "https://yourbrand.com/connected",
    "branding": {"name": "Your Brand", "logo_url": "https://yourbrand.com/logo.png"},
    "account_id": None,
    "url": "https://connect.fopost.com/s/cs_1",
    "expires_at": "2026-10-18T13:00:00.000Z",
    "used_at": None,
    "created_at": "2026-10-18T12:00:00.000Z",
}


@respx.mock
def test_create_sends_camel_case_body_and_get_polls(client: Fopost) -> None:
    create = respx.post(f"{BASE_URL}/connect-sessions").mock(
        return_value=httpx.Response(201, json=SESSION)
    )
    get = respx.get(f"{BASE_URL}/connect-sessions/cs_1").mock(
        return_value=httpx.Response(
            200, json={"data": {**SESSION, "status": "used", "account_id": "acc_9"}}
        )
    )

    session = client.connect_sessions.create(
        workspace_id="ws_1",
        external_user_id="user-42",
        platforms=["twitter", "linkedin"],
        redirect_url="https://yourbrand.com/connected",
        branding={"name": "Your Brand", "logo_url": "https://yourbrand.com/logo.png"},
    )

    assert json.loads(create.calls.last.request.content) == {
        "workspaceId": "ws_1",
        "externalUserId": "user-42",
        "platforms": ["twitter", "linkedin"],
        "redirectUrl": "https://yourbrand.com/connected",
        "branding": {"name": "Your Brand", "logoUrl": "https://yourbrand.com/logo.png"},
    }
    assert session.id == "cs_1" and session.status == "pending"
    assert session.url == "https://connect.fopost.com/s/cs_1"
    assert session.branding is not None and session.branding.logo_url.endswith("logo.png")

    polled = client.connect_sessions.get("cs_1")
    assert get.called
    assert polled.status == "used" and polled.account_id == "acc_9"
