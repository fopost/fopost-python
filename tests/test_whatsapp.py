"""The WhatsApp resource calls the paths the API serves, and nothing else."""

from __future__ import annotations

import httpx
import respx

from tests.conftest import BASE_URL


def _ok(payload: object) -> httpx.Response:
    return httpx.Response(200, json={"data": payload})


@respx.mock
def test_a_template_create_returns_the_review_status_the_platform_gave_it(client) -> None:  # type: ignore[no-untyped-def]
    route = respx.post(f"{BASE_URL}/accounts/a1/whatsapp/templates").mock(
        return_value=_ok(
            {
                "id": "tpl-1",
                "name": "order_shipped",
                "language": "en_US",
                "category": "UTILITY",
                "status": "PENDING",
                "rejected_reason": None,
                "components": [],
                "quality_score": None,
            }
        )
    )
    template = client.whatsapp.create_template(
        "a1",
        name="order_shipped",
        language="en_US",
        category="UTILITY",
        components=[{"type": "BODY", "text": "On its way."}],
    )

    assert route.called
    # Nothing marks a template approved but the platform.
    assert template.status == "PENDING"
    assert template.name == "order_shipped"


@respx.mock
def test_the_sandbox_session_never_carries_the_whole_number(client) -> None:  # type: ignore[no-untyped-def]
    respx.post(f"{BASE_URL}/whatsapp/sandbox/sessions").mock(
        return_value=_ok(
            {
                "id": "ses-1",
                "status": "invited",
                "phone_number_last4": "4567",
                "invited_at": "2026-09-20T10:00:00Z",
                "activated_at": None,
                "expires_at": "2026-09-21T10:00:00Z",
            }
        )
    )
    session = client.whatsapp.create_sandbox_session(workspace_id="ws", phone_number="+15551234567")

    assert session.phone_number_last4 == "4567"
    assert not hasattr(session, "phone_number")
