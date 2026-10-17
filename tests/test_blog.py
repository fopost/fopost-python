from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx

from fopost import Fopost, FopostError, PaymentRequiredError
from tests.conftest import BASE_URL

SETTINGS_FIXTURE: dict[str, Any] = {
    "siteUrl": "https://yourbrand.com",
    "topic": "Running shoes",
    "audience": "Weekend runners",
    "language": "en",
    "locationCode": 2840,
    "cadencePerWeek": 2,
    "reviewHoldDays": 3,
    "autoPublish": False,
    "imageTier": "standard",
    "inBodyImages": 2,
    "minWords": 900,
    "maxWords": 1600,
    "brandVoiceId": None,
    "targetKind": "website",
    "targetAccountId": None,
    "targetPlatform": None,
    "websiteUrl": "https://yourbrand.com/api/fopost",
    "hasWebsiteSecret": True,
    "keywordDataAvailable": True,
    "updatedAt": "2026-10-10T09:00:00.000Z",
}

KEYWORD_FIXTURE: dict[str, Any] = {
    "id": "kw_1",
    "keyword": "best trail running shoes",
    "searchVolume": 12000,
    "difficulty": 41,
    "cpc": 1.2,
    "intent": "commercial",
    "source": "provider",
    "status": "planned",
    "plannedFor": "2026-10-14",
    "createdAt": "2026-10-10T09:00:00.000Z",
}

ARTICLE_FIXTURE: dict[str, Any] = {
    "id": "art_1",
    "title": "The Best Trail Running Shoes of the Year",
    "slug": "best-trail-running-shoes",
    "keyword": "best trail running shoes",
    "excerpt": "What to look for on rock, mud and root.",
    "metaTitle": None,
    "metaDescription": None,
    "featuredImage": {"mediaId": "med_1", "url": "https://cdn.test/f.jpg", "alt": "Trail"},
    "tags": ["shoes", "trail"],
    "wordCount": 1240,
    "status": "draft",
    "origin": "plan",
    "reviewUntil": "2026-10-13T09:00:00.000Z",
    "publishAt": None,
    "publishedAt": None,
    "publishedUrl": None,
    "error": None,
    "createdAt": "2026-10-10T09:00:00.000Z",
    "updatedAt": "2026-10-10T10:00:00.000Z",
}

ARTICLE_FULL_FIXTURE: dict[str, Any] = {
    **ARTICLE_FIXTURE,
    "instructions": "Mention the return policy.",
    "outline": ["Why fit matters", "Our picks"],
    "brief": {"questions": ["Are trail shoes waterproof?"], "competitors": []},
    "bodyMarkdown": "# The Best Trail Running Shoes\n\nFit first.",
    "bodyHtml": "<h1>The Best Trail Running Shoes</h1><p>Fit first.</p>",
    "images": [
        {"mediaId": "med_2", "url": "https://cdn.test/1.jpg", "alt": "Mud", "position": 1},
    ],
}


def _json(request: httpx.Request) -> dict[str, Any]:
    return dict(json.loads(request.content))


# ── Settings ──────────────────────────────────────────────────────


@respx.mock
def test_settings_round_trip(client: Fopost) -> None:
    get_route = respx.get(f"{BASE_URL}/blog/settings").mock(
        return_value=httpx.Response(200, json={"data": SETTINGS_FIXTURE})
    )
    patch_route = respx.patch(f"{BASE_URL}/blog/settings").mock(
        return_value=httpx.Response(
            200, json={"data": SETTINGS_FIXTURE, "websiteSecret": "whsec_once"}
        )
    )
    rotate_route = respx.post(f"{BASE_URL}/blog/settings/website-secret").mock(
        return_value=httpx.Response(200, json={"data": {"websiteSecret": "whsec_new"}})
    )
    test_route = respx.post(f"{BASE_URL}/blog/settings/website-test").mock(
        return_value=httpx.Response(
            502, json={"data": {"ok": False, "status": 500, "error": "upstream failed"}}
        )
    )

    settings = client.blog.get_settings("ws_1")
    assert settings.cadence_per_week == 2
    assert settings.target_kind == "website"
    assert settings.has_website_secret is True
    assert dict(get_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}
    assert get_route.calls.last.request.headers["X-API-Key"] == "osk_test_key"

    updated = client.blog.update_settings(
        "ws_1", website_url="https://yourbrand.com/api/fopost", cadence_per_week=2, topic=None
    )
    assert updated.website_secret == "whsec_once"
    assert updated.settings.site_url == "https://yourbrand.com"
    assert _json(patch_route.calls.last.request) == {
        "workspaceId": "ws_1",
        "websiteUrl": "https://yourbrand.com/api/fopost",
        "cadencePerWeek": 2,
        "topic": None,
    }

    assert client.blog.rotate_website_secret("ws_1") == "whsec_new"
    assert _json(rotate_route.calls.last.request) == {"workspaceId": "ws_1"}

    with pytest.raises(FopostError) as err:
        client.blog.test_website("ws_1")
    assert err.value.status == 502
    assert _json(test_route.calls.last.request) == {"workspaceId": "ws_1"}


@respx.mock
def test_website_test_reports_the_outcome(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/blog/settings/website-test").mock(
        return_value=httpx.Response(200, json={"data": {"ok": True, "status": 200, "error": None}})
    )
    result = client.blog.test_website("ws_1")
    assert result.ok is True and result.status == 200


# ── Keywords ──────────────────────────────────────────────────────


@respx.mock
def test_keywords_round_trip(client: Fopost) -> None:
    list_route = respx.get(f"{BASE_URL}/blog/keywords").mock(
        return_value=httpx.Response(200, json={"data": [KEYWORD_FIXTURE]})
    )
    plan_route = respx.post(f"{BASE_URL}/blog/keywords/plan").mock(
        return_value=httpx.Response(202, json={"data": {"status": "queued"}})
    )
    add_route = respx.post(f"{BASE_URL}/blog/keywords").mock(
        return_value=httpx.Response(201, json={"data": KEYWORD_FIXTURE})
    )
    patch_route = respx.patch(f"{BASE_URL}/blog/keywords/kw_1").mock(
        return_value=httpx.Response(200, json={"data": {**KEYWORD_FIXTURE, "status": "dismissed"}})
    )
    delete_route = respx.delete(f"{BASE_URL}/blog/keywords/kw_1").mock(
        return_value=httpx.Response(204)
    )

    keywords = client.blog.list_keywords("ws_1", status=["suggested", "planned"], limit=50)
    assert keywords[0].search_volume == 12000
    assert str(keywords[0].planned_for) == "2026-10-14"
    assert dict(list_route.calls.last.request.url.params) == {
        "workspaceId": "ws_1",
        "status": "suggested,planned",
        "limit": "50",
    }

    assert client.blog.plan_keywords("ws_1", seeds=["trail shoes"]) == {"status": "queued"}
    assert _json(plan_route.calls.last.request) == {"workspaceId": "ws_1", "seeds": ["trail shoes"]}

    added = client.blog.add_keyword("ws_1", keyword="trail shoes", planned_for="2026-10-14")
    assert added.id == "kw_1"
    assert _json(add_route.calls.last.request) == {
        "workspaceId": "ws_1",
        "keyword": "trail shoes",
        "plannedFor": "2026-10-14",
    }

    dismissed = client.blog.update_keyword("ws_1", "kw_1", status="dismissed", planned_for=None)
    assert dismissed.status == "dismissed"
    assert dict(patch_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}
    assert _json(patch_route.calls.last.request) == {"status": "dismissed", "plannedFor": None}

    assert client.blog.delete_keyword("ws_1", "kw_1") is None
    assert dict(delete_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}


@respx.mock
def test_planning_on_an_empty_balance_is_a_payment_error(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/blog/keywords/plan").mock(
        return_value=httpx.Response(
            402,
            json={
                "error": "insufficient_credits",
                "message": "Your balance ran out.",
                "upgrade_url": "/settings/billing",
            },
        )
    )
    with pytest.raises(PaymentRequiredError) as err:
        client.blog.plan_keywords("ws_1")
    assert err.value.code == "insufficient_credits"
    assert err.value.upgrade_url == "/settings/billing"


# ── Articles ──────────────────────────────────────────────────────


@respx.mock
def test_articles_round_trip(client: Fopost) -> None:
    list_route = respx.get(f"{BASE_URL}/blog/articles").mock(
        return_value=httpx.Response(200, json={"data": [ARTICLE_FIXTURE]})
    )
    create_route = respx.post(f"{BASE_URL}/blog/articles").mock(
        return_value=httpx.Response(202, json={"data": {**ARTICLE_FIXTURE, "status": "queued"}})
    )
    get_route = respx.get(f"{BASE_URL}/blog/articles/art_1").mock(
        return_value=httpx.Response(200, json={"data": ARTICLE_FULL_FIXTURE})
    )
    patch_route = respx.patch(f"{BASE_URL}/blog/articles/art_1").mock(
        return_value=httpx.Response(200, json={"data": ARTICLE_FULL_FIXTURE})
    )
    regenerate_route = respx.post(f"{BASE_URL}/blog/articles/art_1/regenerate").mock(
        return_value=httpx.Response(202, json={"data": {**ARTICLE_FIXTURE, "status": "writing"}})
    )
    publish_route = respx.post(f"{BASE_URL}/blog/articles/art_1/publish").mock(
        return_value=httpx.Response(202, json={"data": {**ARTICLE_FIXTURE, "status": "publishing"}})
    )
    reject_route = respx.post(f"{BASE_URL}/blog/articles/art_1/reject").mock(
        return_value=httpx.Response(200, json={"data": {**ARTICLE_FIXTURE, "status": "rejected"}})
    )
    delete_route = respx.delete(f"{BASE_URL}/blog/articles/art_1").mock(
        return_value=httpx.Response(204)
    )

    articles = client.blog.list_articles("ws_1", status="draft", limit=10)
    assert articles[0].word_count == 1240
    assert articles[0].featured_image is not None
    assert articles[0].featured_image.media_id == "med_1"
    assert dict(list_route.calls.last.request.url.params) == {
        "workspaceId": "ws_1",
        "status": "draft",
        "limit": "10",
    }

    queued = client.blog.request_article(
        "ws_1", keyword_id="kw_1", instructions="Mention the return policy."
    )
    assert queued.status == "queued"
    assert _json(create_route.calls.last.request) == {
        "workspaceId": "ws_1",
        "keywordId": "kw_1",
        "instructions": "Mention the return policy.",
    }

    full = client.blog.get_article("ws_1", "art_1")
    assert full.body_markdown.startswith("# The Best")
    assert full.images[0].position == 1
    assert full.brief is not None and full.brief["questions"] == ["Are trail shoes waterproof?"]
    assert dict(get_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}

    client.blog.update_article(
        "ws_1", "art_1", title="New title", tags=["shoes"], publish_at="2026-10-15T09:00:00Z"
    )
    assert dict(patch_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}
    assert _json(patch_route.calls.last.request) == {
        "title": "New title",
        "tags": ["shoes"],
        "publishAt": "2026-10-15T09:00:00Z",
    }

    assert client.blog.regenerate_article("ws_1", "art_1").status == "writing"
    assert dict(regenerate_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}
    assert client.blog.publish_article("ws_1", "art_1").status == "publishing"
    assert dict(publish_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}
    assert client.blog.reject_article("ws_1", "art_1").status == "rejected"
    assert dict(reject_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}
    assert client.blog.delete_article("ws_1", "art_1") is None
    assert dict(delete_route.calls.last.request.url.params) == {"workspaceId": "ws_1"}


@respx.mock
def test_publishing_without_a_target_is_a_conflict(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/blog/articles/art_1/publish").mock(
        return_value=httpx.Response(
            409, json={"error": "no_target", "message": "Choose where articles go first."}
        )
    )
    with pytest.raises(FopostError) as err:
        client.blog.publish_article("ws_1", "art_1")
    assert type(err.value) is FopostError
    assert err.value.status == 409
    assert err.value.code == "no_target"
