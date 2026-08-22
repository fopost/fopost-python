from __future__ import annotations

import httpx
import pytest
import respx

from fopost import (
    AuthenticationError,
    NotFoundError,
    Fopost,
    FopostError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
)
from tests.conftest import BASE_URL

CASES = [
    (401, "unauthorized", "Invalid API key", AuthenticationError),
    (402, "no_subscription", "AI features require an active subscription.", PaymentRequiredError),
    (403, "forbidden", "Token does not have 'posts' permission", PermissionDeniedError),
    (404, "not_found", "Post not found", NotFoundError),
]


@pytest.mark.parametrize(("status", "code", "message", "expected"), CASES)
@respx.mock
def test_error_envelope_maps_to_a_specific_class(
    client: Fopost, status: int, code: str, message: str, expected: type[FopostError]
) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(status, json={"error": code, "message": message})
    )

    with pytest.raises(expected) as excinfo:
        client.posts.get("post_1")

    error = excinfo.value
    assert isinstance(error, FopostError)
    assert error.status == status
    assert error.code == code
    assert error.message == message
    assert str(error) == f"[{status} ({code})] {message}"


@respx.mock
def test_a_429_that_survives_every_retry_raises_rate_limit_error(
    client: Fopost, no_sleep: list[float]
) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "7"},
            json={"error": "too_many_requests", "message": "Rate limit exceeded."},
        )
    )

    with pytest.raises(RateLimitError) as excinfo:
        client.posts.get("post_1")

    assert excinfo.value.status == 429
    assert excinfo.value.retry_after == 7.0


@respx.mock
def test_an_unmapped_status_raises_the_base_error(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(500, json={"error": "AI service unavailable"})
    )

    with pytest.raises(FopostError) as excinfo:
        client.posts.get("post_1")

    assert type(excinfo.value) is FopostError
    assert excinfo.value.status == 500
    assert excinfo.value.message == "AI service unavailable"


@respx.mock
def test_a_non_json_error_body_still_carries_its_text(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(502, text="upstream is down")
    )

    with pytest.raises(FopostError) as excinfo:
        client.posts.get("post_1")

    assert excinfo.value.status == 502
    assert excinfo.value.message == "upstream is down"


@respx.mock
def test_a_non_json_success_body_is_rejected(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(200, text="<html>login</html>")
    )

    with pytest.raises(FopostError, match="Expected a JSON response"):
        client.posts.get("post_1")
