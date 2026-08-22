from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest
import respx

from fopost import Fopost, FopostError, RateLimitError
from tests.conftest import API_KEY, BASE_URL, POST_FIXTURE


@respx.mock
def test_a_429_is_retried_and_the_retry_after_wait_is_honored(
    client: Fopost, no_sleep: list[float]
) -> None:
    route = respx.get(f"{BASE_URL}/posts/post_1").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(200, json=POST_FIXTURE),
        ]
    )

    post = client.posts.get("post_1")

    assert post.id == "post_1"
    assert route.call_count == 2
    assert no_sleep == [2.0]


@respx.mock
def test_retries_stop_after_three_attempts(client: Fopost, no_sleep: list[float]) -> None:
    route = respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "1"})
    )

    with pytest.raises(RateLimitError):
        client.posts.get("post_1")

    assert route.call_count == 3
    assert no_sleep == [1.0, 1.0]


@respx.mock
def test_max_retries_is_configurable(no_sleep: list[float]) -> None:
    route = respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "1"})
    )

    with Fopost(api_key=API_KEY, base_url=BASE_URL, max_retries=1) as client:
        with pytest.raises(RateLimitError):
            client.posts.get("post_1")

    assert route.call_count == 1
    assert no_sleep == []


@respx.mock
def test_a_missing_retry_after_falls_back_to_one_second(
    client: Fopost, no_sleep: list[float]
) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        side_effect=[
            httpx.Response(429),
            httpx.Response(200, json=POST_FIXTURE),
        ]
    )

    client.posts.get("post_1")

    assert no_sleep == [1.0]


@respx.mock
def test_a_http_date_retry_after_is_parsed(client: Fopost, no_sleep: list[float]) -> None:
    when = datetime.now(timezone.utc) + timedelta(seconds=5)
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": format_datetime(when, usegmt=True)}),
            httpx.Response(200, json=POST_FIXTURE),
        ]
    )

    client.posts.get("post_1")

    assert len(no_sleep) == 1
    assert 3.0 <= no_sleep[0] <= 6.0


@respx.mock
def test_a_very_long_retry_after_is_capped(client: Fopost, no_sleep: list[float]) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "9999"}),
            httpx.Response(200, json=POST_FIXTURE),
        ]
    )

    client.posts.get("post_1")

    assert no_sleep == [60.0]


@respx.mock
def test_other_statuses_are_not_retried(client: Fopost, no_sleep: list[float]) -> None:
    route = respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(500, json={"error": "server_error"})
    )

    with pytest.raises(FopostError):
        client.posts.get("post_1")

    assert route.call_count == 1
    assert no_sleep == []
