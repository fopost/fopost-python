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


@respx.mock
def test_dashboard_reads_send_filters_and_decode(client: Fopost) -> None:
    overview = respx.get(f"{BASE_URL}/analytics/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total_accounts": 2,
                "total_followers": 1500,
                "deltas": {"followers": 3.5},
                "today_stats": {"posts": 1, "follower_change": 4, "engagement": 20},
                "platforms": [{"platform": "twitter", "accounts": 1, "followers": 900}],
                "accounts": [
                    {
                        "account_id": "acc_1",
                        "platform": "twitter",
                        "username": "yourbrand",
                        "name": "Your Brand",
                        "followers": 900,
                        "history": [{"date": "2026-10-18", "followers": 900}],
                    }
                ],
            },
        )
    )
    series = respx.get(f"{BASE_URL}/analytics/time-series").mock(
        return_value=httpx.Response(
            200, json={"days": 7, "series": [{"date": "2026-10-18", "engagements": 5}]}
        )
    )
    top = respx.get(f"{BASE_URL}/analytics/top-posts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "rank": 1,
                        "post_id": "post_1",
                        "source": "fopost",
                        "metrics": {"engagements": 50},
                        "labels": [{"id": "lbl_1", "name": "Launch", "color": "#000"}],
                    }
                ]
            },
        )
    )
    labels = respx.get(f"{BASE_URL}/analytics/labels").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"label_id": "lbl_1", "name": "Launch", "post_count": 2}]},
        )
    )
    table = respx.get(f"{BASE_URL}/analytics/posts-table").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "post_id": "post_1",
                        "status": "published",
                        "platforms": [{"platform": "twitter", "delivery_status": "published"}],
                        "delivery_summary": {"total": 1, "published": 1},
                    }
                ],
                "meta": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1},
                "summary": {"published": 1, "total": 1},
            },
        )
    )
    streak = respx.get(f"{BASE_URL}/analytics/posting-streak").mock(
        return_value=httpx.Response(
            200, json={"streak": [{"date": "2026-10-18", "count": 2, "published_count": 2}]}
        )
    )
    demographics = respx.get(f"{BASE_URL}/analytics/demographics").mock(
        return_value=httpx.Response(
            200,
            json={
                "audience": "engaged",
                "dimensions": {"age": [{"key": "25-34", "value": 40, "share": 0.4}]},
                "contributing_accounts": [{"account_id": "acc_1", "platform": "instagram"}],
                "unsupported_accounts": [],
            },
        )
    )
    inbox = respx.get(f"{BASE_URL}/analytics/inbox").mock(
        return_value=httpx.Response(
            200,
            json={
                "totals": {"received": 10, "sent": 8, "median_response_minutes": 12.5},
                "heatmap": [{"weekday": 1, "hour": 9, "count": 3}],
                "time_zone": "Europe/Zagreb",
            },
        )
    )
    collect = respx.post(f"{BASE_URL}/analytics/collect").mock(
        return_value=httpx.Response(
            200,
            json={
                "accounts": 2,
                "posts": 5,
                "demographics": 1,
                "errors": 1,
                "error_details": [
                    {"account_id": "acc_2", "stage": "account", "action": "reconnect"}
                ],
            },
        )
    )

    o = client.analytics.overview(days=30, workspace_id="ws_1")
    assert o.total_followers == 1500 and o.accounts[0].history[0].followers == 900
    assert dict(overview.calls.last.request.url.params) == {"days": "30", "workspace_id": "ws_1"}

    ts = client.analytics.time_series(from_="2026-10-01", to="2026-10-18")
    assert ts.series[0].engagements == 5
    assert dict(series.calls.last.request.url.params) == {"from": "2026-10-01", "to": "2026-10-18"}

    posts = client.analytics.top_posts(limit=1, sort="recent", label="Launch")
    assert posts[0].metrics is not None and posts[0].metrics.engagements == 50
    assert dict(top.calls.last.request.url.params) == {
        "limit": "1",
        "sort": "recent",
        "label": "Launch",
    }

    assert client.analytics.labels(days=7)[0].post_count == 2 and labels.called

    rows = client.analytics.posts_table(account_id="acc_1")
    assert rows.items[0].platforms[0].delivery_status == "published"
    assert rows.meta.total == 1 and rows.summary is not None and rows.summary.published == 1
    assert dict(table.calls.last.request.url.params) == {
        "page": "1",
        "per_page": "20",
        "account_id": "acc_1",
    }

    assert client.analytics.posting_streak(workspace_id="ws_1")[0].published_count == 2
    assert streak.called

    d = client.analytics.demographics(audience="engaged")
    assert d.dimensions.age[0].share == 0.4 and d.contributing_accounts[0].platform == "instagram"
    assert dict(demographics.calls.last.request.url.params) == {"audience": "engaged"}

    ia = client.analytics.inbox(days=7, tz="Europe/Zagreb")
    assert ia.totals is not None and ia.totals.median_response_minutes == 12.5
    assert ia.heatmap[0].hour == 9
    assert dict(inbox.calls.last.request.url.params) == {"days": "7", "tz": "Europe/Zagreb"}

    c = client.analytics.collect(workspace_id="ws_1")
    assert c.errors == 1 and c.error_details[0].action == "reconnect"
    assert dict(collect.calls.last.request.url.params) == {"workspace_id": "ws_1"}
