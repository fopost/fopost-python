from __future__ import annotations

from typing import Any

import pytest

from owlstack import Owlstack

BASE_URL = "https://api.test.owlstack.app/api/v1"
API_KEY = "osk_test_key"


@pytest.fixture
def client() -> Any:
    with Owlstack(api_key=API_KEY, base_url=BASE_URL) as c:
        yield c


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record retry waits instead of actually sleeping."""
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr("owlstack._http._sleep", fake_sleep)
    return slept


POST_FIXTURE: dict[str, Any] = {
    "id": "post_1",
    "workspace_id": "ws_1",
    "status": "draft",
    "content_type": "post",
    "schedule_at": None,
    "repeatable": False,
    "title": None,
    "summary": None,
    "content": [{"id": 1, "text": "Hello from Python", "media": [], "position": 0}],
    "accounts": [
        {
            "id": "acc_1",
            "platform": "twitter",
            "username": "owlstack",
            "name": "OwlStack",
            "publish_status": "pending",
            "attempts": 0,
            "max_attempts": 3,
        }
    ],
    "labels": [],
    "settings": {},
    "created_at": "2026-08-12T10:00:00.000Z",
    "updated_at": "2026-08-12T10:00:00.000Z",
}

ACCOUNT_FIXTURE: dict[str, Any] = {
    "id": "acc_1",
    "workspaceId": "ws_1",
    "platform": "twitter",
    "username": "owlstack",
    "name": "OwlStack",
    "avatar": None,
    "isPrimary": True,
    "active": True,
    "healthStatus": "healthy",
    "lastHealthCheck": "2026-08-12T09:00:00.000Z",
}

WORKSPACE_FIXTURE: dict[str, Any] = {
    "id": "ws_1",
    "name": "Acme",
    "slug": "acme",
    "type": "brand",
    "timezone": "UTC",
    "language": "en",
    "require_approval": False,
    "ai_alt_text_enabled": True,
    "brand_color": "#4F46E5",
    "role": "owner",
    "created_at": "2026-01-01T00:00:00.000Z",
    "accounts": [ACCOUNT_FIXTURE],
}

LABEL_FIXTURE: dict[str, Any] = {
    "id": "lbl_1",
    "name": "Launch",
    "color": "#4F46E5",
    "workspace": {"id": "ws_1", "name": "Acme", "slug": "acme"},
}
