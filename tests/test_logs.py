from __future__ import annotations

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL


@respx.mock
def test_list_sends_filters_and_decodes_cursor_and_summary(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/logs").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 42,
                        "workspace_id": "ws_1",
                        "time": "2026-10-18T12:00:00.000Z",
                        "auth_method": "api_key",
                        "method": "POST",
                        "route": "/v1/posts",
                        "path": "/v1/posts",
                        "status_code": 500,
                        "duration_ms": 80,
                        "platform": None,
                        "message": "boom",
                    }
                ],
                "meta": {"next_cursor": "41", "has_more": True},
                "summary": {
                    "since": "2026-10-11T12:00:00.000Z",
                    "total": 10,
                    "errors": 1,
                    "buckets": [{"at": "2026-10-18T12:00:00.000Z", "total": 3, "errors": 1}],
                },
            },
        )
    )

    page = client.logs.list(workspace_id="ws_1", status="failed", days=7, limit=1, before=43)

    assert dict(route.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "status": "failed",
        "days": "7",
        "limit": "1",
        "before": "43",
    }
    assert page.items[0].id == 42 and page.items[0].status_code == 500
    assert page.meta.next_cursor == "41" and page.meta.has_more is True
    assert page.summary is not None and page.summary.buckets[0].errors == 1
