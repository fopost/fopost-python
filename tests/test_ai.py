from __future__ import annotations

import json

import httpx
import pytest
import respx

from fopost import Fopost, PaymentRequiredError
from tests.conftest import BASE_URL


@respx.mock
def test_credits_returns_the_balance(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/ai/credits").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "creditsRemaining": 420,
                    "creditsUsed": 80,
                    "creditsTotal": 500,
                    "periodStart": "2026-08-01T00:00:00.000Z",
                    "periodEnd": "2026-09-01T00:00:00.000Z",
                }
            },
        )
    )

    balance = client.ai.credits()

    assert balance.credits_remaining == 420
    assert balance.credits_used == 80
    assert balance.credits_total == 500
    assert balance.period_start is not None


@respx.mock
def test_generate_caption_sends_snake_case_and_drops_unset(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ai/generate-caption").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "caption": "Shipping something good.",
                    "credits": {"charged": 1, "remaining": 419},
                }
            },
        )
    )

    result = client.ai.generate_caption(
        current_caption="shipping a new feature",
        platforms=["twitter", "linkedin"],
        char_limit=280,
    )

    assert result.caption == "Shipping something good."
    assert result.credits is not None
    assert result.credits.charged == 1
    assert json.loads(route.calls.last.request.content) == {
        "current_caption": "shipping a new feature",
        "platforms": ["twitter", "linkedin"],
        "char_limit": 280,
    }


@respx.mock
def test_rewrite_returns_one_variant_per_platform(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ai/rewrite").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "results": [
                        {"platform": "twitter", "content": "Short version", "credits": 1},
                        {"platform": "linkedin", "content": "Longer version", "credits": 1},
                    ],
                    "credits": {"charged": 2, "remaining": 417},
                }
            },
        )
    )

    result = client.ai.rewrite(content="A long draft", platforms=["twitter", "linkedin"])

    assert [v.platform for v in result.results] == ["twitter", "linkedin"]
    assert result.credits is not None
    assert result.credits.charged == 2
    assert json.loads(route.calls.last.request.content) == {
        "content": "A long draft",
        "platforms": ["twitter", "linkedin"],
    }


@respx.mock
def test_repurpose_url_returns_a_post_per_platform(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/ai/repurpose-url").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "url": "https://example.com/blog/post",
                    "title": "How we ship",
                    "posts": {"twitter": "Thread starter", "bluesky": "Short take"},
                    "credits": {"charged": 6, "remaining": 411},
                }
            },
        )
    )

    result = client.ai.repurpose_url(
        url="https://example.com/blog/post", platforms=["twitter", "bluesky"]
    )

    assert result.title == "How we ship"
    assert result.posts["twitter"] == "Thread starter"


@respx.mock
def test_out_of_credits_raises_payment_required_with_the_upgrade_url(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/ai/rewrite").mock(
        return_value=httpx.Response(
            402,
            json={
                "error": "insufficient_credits",
                "message": "You have run out of AI credits.",
                "upgrade_url": "/settings/plans",
            },
        )
    )

    with pytest.raises(PaymentRequiredError) as excinfo:
        client.ai.rewrite(content="A long draft", platforms=["twitter"])

    assert excinfo.value.status == 402
    assert excinfo.value.code == "insufficient_credits"
    assert excinfo.value.upgrade_url == "/settings/plans"
