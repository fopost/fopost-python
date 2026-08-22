from __future__ import annotations

import httpx
import pytest
import respx

import fopost
from fopost import DEFAULT_BASE_URL, Fopost
from tests.conftest import API_KEY, BASE_URL, POST_FIXTURE


def test_the_api_key_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOPOST_API_KEY", raising=False)

    with pytest.raises(ValueError, match="api_key is required"):
        Fopost()


def test_the_api_key_falls_back_to_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOPOST_API_KEY", "osk_from_env")

    with Fopost() as client:
        assert client._http.api_key == "osk_from_env"


def test_the_default_base_url_includes_the_api_version() -> None:
    assert DEFAULT_BASE_URL == "https://api.fopost.com/api/v1"

    with Fopost(api_key=API_KEY) as client:
        assert client.base_url == DEFAULT_BASE_URL


def test_a_trailing_slash_on_the_base_url_does_not_double_up() -> None:
    with Fopost(api_key=API_KEY, base_url=f"{BASE_URL}/") as client:
        assert client.base_url == BASE_URL


def test_every_namespace_is_bound() -> None:
    with Fopost(api_key=API_KEY) as client:
        for name in ("posts", "accounts", "workspaces", "labels", "ai"):
            assert getattr(client, name) is not None


def test_fopost_is_exported_under_the_typescript_spelling_too() -> None:
    assert fopost.FoPost is fopost.Fopost


@respx.mock
def test_every_request_carries_the_api_key_and_user_agent(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(200, json=POST_FIXTURE)
    )

    client.posts.get("post_1")

    headers = route.calls.last.request.headers
    assert headers["x-api-key"] == API_KEY
    assert headers["user-agent"] == "fopost-python"
    assert headers["accept"] == "application/json"


@respx.mock
def test_request_reaches_an_endpoint_the_sdk_does_not_wrap(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/analytics/summary").mock(
        return_value=httpx.Response(200, json={"data": {"impressions": 12}})
    )

    assert client.request("GET", "/analytics/summary") == {"data": {"impressions": 12}}


def test_max_retries_must_be_at_least_one() -> None:
    with pytest.raises(ValueError, match="max_retries"):
        Fopost(api_key=API_KEY, max_retries=0)


@respx.mock
def test_an_injected_http_client_is_used_and_left_open() -> None:
    respx.get(f"{BASE_URL}/workspaces").mock(return_value=httpx.Response(200, json={"data": []}))

    transport_client = httpx.Client(timeout=5.0)
    client = Fopost(api_key=API_KEY, base_url=BASE_URL, http_client=transport_client)
    client.workspaces.list()
    client.close()

    assert not transport_client.is_closed
    transport_client.close()
