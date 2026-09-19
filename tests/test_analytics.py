from __future__ import annotations

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL


@respx.mock
def test_decay_parses_the_bands_and_half_life(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/analytics/decay").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "days": 30,
                    "postsMeasured": 2,
                    "halfLifeBucket": "1h_3h",
                    "bands": [
                        {
                            "bucket": "under_1h",
                            "label": "First hour",
                            "posts": 2,
                            "avgEngagements": 25,
                            "avgImpressions": 300,
                            "shareOfFinal": 0.3,
                        },
                        {
                            "bucket": "6h_12h",
                            "label": "6-12 hours",
                            "posts": 0,
                            "avgEngagements": 0,
                            "avgImpressions": 0,
                            "shareOfFinal": None,
                        },
                    ],
                }
            },
        )
    )

    decay = client.analytics.decay(days=30, account_id="acc_1")

    assert route.call_count == 1
    assert dict(route.calls[0].request.url.params) == {"days": "30", "accountId": "acc_1"}
    assert decay.half_life_bucket == "1h_3h"
    assert decay.bands[0].share_of_final == 0.3
    # A band nothing was measured in reports no share rather than zero
    assert decay.bands[1].share_of_final is None


@respx.mock
def test_frequency_parses_weeks_and_the_best_cadence(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/analytics/frequency").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "days": 90,
                    "weeks": [
                        {
                            "weekStart": "2026-03-02",
                            "posts": 2,
                            "engagements": 240,
                            "avgEngagementsPerPost": 120,
                        }
                    ],
                    "bands": [
                        {
                            "band": "under_3",
                            "label": "1-2 a week",
                            "weeks": 1,
                            "posts": 2,
                            "avgPostsPerWeek": 2,
                            "avgEngagementsPerPost": 120,
                            "engagementRate": 0.12,
                        }
                    ],
                    "best": {
                        "band": "under_3",
                        "label": "1-2 a week",
                        "avgEngagementsPerPost": 120,
                    },
                }
            },
        )
    )

    frequency = client.analytics.frequency(days=90)

    assert frequency.weeks[0].week_start == "2026-03-02"
    assert frequency.best is not None
    assert frequency.best.label == "1-2 a week"
    assert frequency.bands[0].engagement_rate == 0.12


@respx.mock
def test_timeline_escapes_a_permalink_into_the_path(client: Fopost) -> None:
    route = respx.get(
        f"{BASE_URL}/analytics/posts/https%3A%2F%2Fx.com%2Facme%2Fstatus%2F1/timeline"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "postId": None,
                    "deliveries": [
                        {
                            "accountId": "acc_1",
                            "platform": "twitter",
                            "username": "acme",
                            "externalPostId": "1",
                            "postedAt": "2026-03-02T00:00:00.000Z",
                            "points": [
                                {
                                    "at": "2026-03-02T00:30:00.000Z",
                                    "ageMinutes": 30,
                                    "engagements": 40,
                                    "impressions": 400,
                                    "reach": None,
                                    "likes": 30,
                                    "comments": None,
                                    "shares": None,
                                    "videoViews": None,
                                    "delta": {
                                        "impressions": 400,
                                        "reach": 0,
                                        "engagements": 40,
                                        "likes": 30,
                                        "comments": 0,
                                        "shares": 0,
                                    },
                                }
                            ],
                        }
                    ],
                }
            },
        )
    )

    timeline = client.analytics.timeline("https://x.com/acme/status/1")

    assert route.call_count == 1
    assert timeline.post_id is None
    assert timeline.deliveries[0].points[0].age_minutes == 30
    assert timeline.deliveries[0].points[0].delta.engagements == 40


@respx.mock
def test_changes_carries_the_cursor(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/analytics/changes").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "since": "2026-03-02T00:00:00.000Z",
                    "cursor": "2026-03-02T06:00:00.000Z",
                    "hasMore": True,
                    "changes": [
                        {
                            "accountId": "acc_1",
                            "platform": "twitter",
                            "externalPostId": "1",
                            "postId": "post_1",
                            "postedAt": "2026-03-02T00:00:00.000Z",
                            "fetchedAt": "2026-03-02T06:00:00.000Z",
                            "impressions": 900,
                            "reach": None,
                            "engagements": 90,
                            "likes": 70,
                            "comments": 10,
                            "shares": 10,
                        }
                    ],
                }
            },
        )
    )

    page = client.analytics.changes(since="2026-03-02T00:00:00Z", limit=100)

    assert dict(route.calls[0].request.url.params) == {
        "since": "2026-03-02T00:00:00Z",
        "limit": "100",
    }
    assert page.has_more is True
    assert page.changes[0].post_id == "post_1"


@respx.mock
def test_collect_post_reports_each_delivery(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/posts/post_1/analytics/collect").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "collected": 1,
                    "deliveries": [
                        {
                            "accountId": "acc_1",
                            "platform": "twitter",
                            "externalPostId": "1",
                            "collected": True,
                            "fetchedAt": "2026-03-02T00:30:00.000Z",
                            "message": None,
                        }
                    ],
                }
            },
        )
    )

    result = client.analytics.collect_post("post_1")

    assert result.collected == 1
    assert result.deliveries[0].collected is True


@respx.mock
def test_native_posts_returns_a_page(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts/acc_1/native-posts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "externalPostId": "1",
                        "text": "Posted by hand",
                        "permalink": "https://x.com/acme/status/1",
                        "thumbnailUrl": None,
                        "mediaType": None,
                        "postedAt": "2026-03-02T00:00:00.000Z",
                        "fetchedAt": "2026-03-02T06:00:00.000Z",
                        "metrics": {
                            "impressions": 900,
                            "reach": None,
                            "engagements": 90,
                            "likes": 70,
                            "comments": 10,
                            "shares": 10,
                            "videoViews": None,
                        },
                    }
                ],
                "meta": {"page": 1, "perPage": 20, "total": 1},
            },
        )
    )

    page = client.analytics.native_posts("acc_1", page=1, per_page=20)

    assert dict(route.calls[0].request.url.params) == {"page": "1", "per_page": "20"}
    assert len(page) == 1
    assert page[0].permalink == "https://x.com/acme/status/1"
    assert page[0].metrics.engagements == 90
    assert page.meta.total == 1
