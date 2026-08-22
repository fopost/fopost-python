from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
import respx

from fopost import Fopost, Post
from tests.conftest import BASE_URL, POST_FIXTURE


@respx.mock
def test_list_returns_posts_and_meta(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [POST_FIXTURE],
                "meta": {
                    "current_page": 1,
                    "per_page": 30,
                    "total": 1,
                    "last_page": 1,
                    "from": 1,
                    "to": 1,
                },
            },
        )
    )

    page = client.posts.list(workspace_id="ws_1", status="draft")

    assert len(page) == 1
    assert isinstance(page[0], Post)
    assert page[0].id == "post_1"
    assert page[0].content[0].text == "Hello from Python"
    assert page.meta.total == 1
    assert page.meta.from_ == 1

    request = route.calls.last.request
    assert dict(request.url.params) == {
        "workspace_id": "ws_1",
        "status": "draft",
        "page": "1",
        "per_page": "30",
    }
    assert request.headers["x-api-key"] == "osk_test_key"


@respx.mock
def test_get_unwraps_a_bare_post(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(return_value=httpx.Response(200, json=POST_FIXTURE))

    post = client.posts.get("post_1")

    assert post.id == "post_1"
    assert post.workspace_id == "ws_1"
    assert post.created_at == datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)


@respx.mock
def test_create_sends_the_shape_the_api_validates(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(201, json=POST_FIXTURE)
    )

    post = client.posts.create(
        workspace_id="ws_1",
        content="Hello from Python",
        accounts=["acc_1"],
        labels=["lbl_1"],
    )

    assert post.id == "post_1"
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "workspace_id": "ws_1",
        "status": "draft",
        "content": [{"text": "Hello from Python"}],
        "accounts": ["acc_1"],
        "labels": ["lbl_1"],
    }


@respx.mock
def test_create_accepts_account_objects_and_datetimes(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(201, json=POST_FIXTURE)
    )

    client.posts.create(
        workspace_id="ws_1",
        content=[{"text": "Block one"}, "Block two"],
        accounts=[{"id": "acc_1"}, "acc_2"],
        status="scheduled",
        schedule_at=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
    )

    body = json.loads(route.calls.last.request.content)
    assert body["accounts"] == ["acc_1", "acc_2"]
    assert body["content"] == [{"text": "Block one"}, {"text": "Block two"}]
    assert body["schedule_at"] == "2026-09-01T10:00:00Z"


@respx.mock
def test_update_only_sends_named_fields(client: Fopost) -> None:
    route = respx.put(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(200, json=POST_FIXTURE)
    )

    client.posts.update("post_1", title="Renamed")

    assert json.loads(route.calls.last.request.content) == {"title": "Renamed"}


@respx.mock
def test_update_can_clear_a_field(client: Fopost) -> None:
    route = respx.put(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(200, json=POST_FIXTURE)
    )

    client.posts.update("post_1", schedule_at=None)

    assert json.loads(route.calls.last.request.content) == {"schedule_at": None}


@respx.mock
def test_delete_returns_none(client: Fopost) -> None:
    route = respx.delete(f"{BASE_URL}/posts/post_1").mock(return_value=httpx.Response(204))

    assert client.posts.delete("post_1") is None
    assert route.called


@pytest.mark.parametrize("action", ["publish", "cancel", "retry", "preflight"])
@respx.mock
def test_lifecycle_actions_post_to_their_endpoint(client: Fopost, action: str) -> None:
    route = respx.post(f"{BASE_URL}/posts/post_1/{action}").mock(
        return_value=httpx.Response(200, json={"data": {"status": "queued"}})
    )

    result = getattr(client.posts, action)("post_1")

    assert result == {"status": "queued"}
    assert route.called


@respx.mock
def test_deliveries_parses_camel_case_rows(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/posts/post_1/deliveries").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "del_1",
                        "accountId": "acc_1",
                        "status": "published",
                        "platform": "twitter",
                        "accountName": "FoPost",
                        "attempts": 1,
                        "maxAttempts": 3,
                        "externalUrl": "https://x.com/fopost/status/1",
                        "postedAt": "2026-08-12T10:05:00.000Z",
                    }
                ]
            },
        )
    )

    deliveries = client.posts.deliveries("post_1")

    assert len(deliveries) == 1
    assert deliveries[0].account_id == "acc_1"
    assert deliveries[0].max_attempts == 3
    assert deliveries[0].external_url == "https://x.com/fopost/status/1"


@respx.mock
def test_iter_walks_every_page(client: Fopost) -> None:
    def page(number: int, last: int) -> dict[str, object]:
        return {
            "data": [{**POST_FIXTURE, "id": f"post_{number}"}],
            "meta": {"current_page": number, "per_page": 1, "total": last, "last_page": last},
        }

    route = respx.get(f"{BASE_URL}/posts").mock(
        side_effect=[
            httpx.Response(200, json=page(1, 3)),
            httpx.Response(200, json=page(2, 3)),
            httpx.Response(200, json=page(3, 3)),
        ]
    )

    posts = list(client.posts.iter(workspace_id="ws_1", per_page=1))

    assert [p.id for p in posts] == ["post_1", "post_2", "post_3"]
    assert route.call_count == 3
    assert [c.request.url.params["page"] for c in route.calls] == ["1", "2", "3"]


@respx.mock
def test_iter_stops_on_an_empty_page_without_meta(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/posts").mock(
        side_effect=[
            httpx.Response(200, json={"data": [POST_FIXTURE, POST_FIXTURE]}),
            httpx.Response(200, json={"data": []}),
        ]
    )

    posts = list(client.posts.iter(per_page=2))

    assert len(posts) == 2
    assert route.call_count == 2


@respx.mock
def test_iter_pages_exposes_meta(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [POST_FIXTURE],
                "meta": {"current_page": 1, "per_page": 30, "total": 1, "last_page": 1},
            },
        )
    )

    pages = list(client.posts.iter_pages())

    assert len(pages) == 1
    assert pages[0].meta.last_page == 1
