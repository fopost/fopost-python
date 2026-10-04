from __future__ import annotations

import httpx
import pytest
import respx

from fopost import Fopost, FopostError
from tests.conftest import BASE_URL

FACEBOOK_SET = {
    "platform": "facebook",
    "account": {
        "fetched_at": "2026-09-20T02:00:00.000Z",
        "metrics": [
            {
                "key": "page_daily_video_ad_break_earnings",
                "label": "Ad Break Earnings",
                "kind": "currency_usd",
                "value": 42.15,
            },
            {
                "key": "page_impressions_paid",
                "label": "Paid Impressions",
                "kind": "count",
                "value": 1500,
            },
        ],
    },
    "post": {
        "external_post_id": "123_456",
        "fetched_at": "2026-09-20T02:00:00.000Z",
        "metrics": [],
    },
}


@respx.mock
def test_platform_metrics_asks_for_raw_and_parses_the_set(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts/acc_1/insights").mock(
        return_value=httpx.Response(200, json={"data": FACEBOOK_SET})
    )

    metrics = client.accounts.platform_metrics("acc_1")

    assert dict(route.calls.last.request.url.params) == {"raw": "true"}
    assert metrics.platform == "facebook"
    assert metrics.account.fetched_at == "2026-09-20T02:00:00.000Z"
    assert [m.key for m in metrics.account.metrics] == [
        "page_daily_video_ad_break_earnings",
        "page_impressions_paid",
    ]
    assert metrics.account.metrics[0].value == 42.15
    assert metrics.post.external_post_id == "123_456"
    assert metrics.post.metrics == []


@respx.mock
def test_a_series_value_survives_as_a_list(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/insights").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "platform": "youtube",
                    "account": {
                        "fetched_at": None,
                        "metrics": [
                            {
                                "key": "daily_views",
                                "label": "Views by Day",
                                "kind": "series",
                                "value": [{"day": "2026-09-19", "views": 600}],
                            }
                        ],
                    },
                    "post": {"external_post_id": None, "fetched_at": None, "metrics": []},
                }
            },
        )
    )

    metrics = client.accounts.platform_metrics("acc_1")

    assert metrics.account.metrics[0].value == [{"day": "2026-09-19", "views": 600}]
    assert metrics.account.fetched_at is None


@respx.mock
def test_a_pending_metric_grant_raises(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/insights").mock(
        return_value=httpx.Response(
            503,
            json={
                "error": "platform_metrics_unavailable",
                "message": "google-business metrics are not available on this deployment yet.",
            },
        )
    )

    with pytest.raises(FopostError) as err:
        client.accounts.platform_metrics("acc_1")

    assert err.value.status == 503
    assert err.value.code == "platform_metrics_unavailable"
