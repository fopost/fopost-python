"""``client.blog`` — plan keywords, request articles and publish them to a website.

A post goes to a social network; an article goes to a website. Everything here
is an article. Suggesting seeds, planning, requesting and regenerating spend AI
credits and need the ``ai`` scope; publishing needs ``publish``; the rest needs
``posts``. A draft is submitted for approval before it can be published.

The workspace travels as ``workspace_id`` on the query string of reads and per-id
routes and as ``workspaceId`` in the body of the collection ``POST``/``PATCH``
routes. Request bodies are camelCase on the wire and responses snake_case; pass
arguments snake_case here.
"""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    BlogArticle,
    BlogArticleFull,
    BlogKeyword,
    BlogSettings,
    BlogSettingsUpdate,
    BlogWebsiteTest,
    _to_camel,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["BlogResource"]


def _camel_body(fields: dict[str, Any]) -> dict[str, Any]:
    return {_to_camel(key): value for key, value in drop_unset(fields).items()}


def _statuses(status: str | Sequence[str] | None) -> str | None:
    if status is None or isinstance(status, str):
        return status
    return ",".join(status)


class BlogResource(Resource):
    # ── Settings ──────────────────────────────────────────────────

    def get_settings(self, workspace_id: str) -> BlogSettings:
        body = self._http.get("/blog/settings", {"workspace_id": workspace_id})
        return BlogSettings.model_validate(unwrap(body))

    def update_settings(
        self,
        workspace_id: str,
        *,
        site_url: str | None | Any = UNSET,
        topic: str | None | Any = UNSET,
        audience: str | None | Any = UNSET,
        goal: str | None | Any = UNSET,
        focus_topics: str | None | Any = UNSET,
        avoid_topics: str | None | Any = UNSET,
        language: str | Any = UNSET,
        location_code: int | Any = UNSET,
        cadence_per_week: int | Any = UNSET,
        review_hold_days: int | Any = UNSET,
        image_tier: str | Any = UNSET,
        in_body_images: int | Any = UNSET,
        min_words: int | Any = UNSET,
        max_words: int | Any = UNSET,
        brand_voice_id: str | None | Any = UNSET,
        target_kind: str | None | Any = UNSET,
        target_account_id: str | None | Any = UNSET,
        website_url: str | None | Any = UNSET,
    ) -> BlogSettingsUpdate:
        """Patch the settings; an argument left out keeps its value.

        ``website_secret`` on the result is set only the first time
        ``website_url`` is saved. Store it then; it is never shown again.
        ``review_hold_days`` is how many days before its planned date a picked
        keyword starts being written.
        """
        body = _camel_body(
            {
                "site_url": site_url,
                "topic": topic,
                "audience": audience,
                "goal": goal,
                "focus_topics": focus_topics,
                "avoid_topics": avoid_topics,
                "language": language,
                "location_code": location_code,
                "cadence_per_week": cadence_per_week,
                "review_hold_days": review_hold_days,
                "image_tier": image_tier,
                "in_body_images": in_body_images,
                "min_words": min_words,
                "max_words": max_words,
                "brand_voice_id": brand_voice_id,
                "target_kind": target_kind,
                "target_account_id": target_account_id,
                "website_url": website_url,
            }
        )
        body["workspaceId"] = workspace_id
        raw = self._http.patch("/blog/settings", body)
        secret = raw.get("website_secret") if isinstance(raw, dict) else None
        return BlogSettingsUpdate(
            settings=BlogSettings.model_validate(unwrap(raw)), website_secret=secret
        )

    def rotate_website_secret(self, workspace_id: str) -> str:
        """Issue a new website secret; the previous one stops verifying at once."""
        body = self._http.post("/blog/settings/website-secret", {"workspaceId": workspace_id})
        data = unwrap(body)
        return str(data["website_secret"]) if isinstance(data, dict) else ""

    def test_website(self, workspace_id: str) -> BlogWebsiteTest:
        """Send a signed ``article.test`` delivery to the website target.

        A refusal raises a 502 ``website_test_failed`` carrying the site's answer.
        """
        body = self._http.post("/blog/settings/website-test", {"workspaceId": workspace_id})
        return BlogWebsiteTest.model_validate(unwrap(body))

    # ── Keywords ──────────────────────────────────────────────────

    def list_keywords(
        self,
        workspace_id: str,
        *,
        status: str | Sequence[str] | None = None,
        limit: int | None = None,
    ) -> builtins.list[BlogKeyword]:
        body = self._http.get(
            "/blog/keywords",
            {"workspace_id": workspace_id, "status": _statuses(status), "limit": limit},
        )
        return parse_list(BlogKeyword, unwrap(body))

    def suggest_seeds(
        self,
        workspace_id: str,
        *,
        seeds: Sequence[str] | None = None,
        prompt: str | None = None,
    ) -> builtins.list[str]:
        """About 10 search terms from the blog goal and topics.

        Pass the current ``seeds`` (up to 20) to refine them and ``prompt`` (up to
        500 characters) to steer. An empty balance raises ``PaymentRequiredError``.
        """
        payload: dict[str, Any] = {"workspaceId": workspace_id}
        if seeds is not None:
            payload["seeds"] = builtins.list(seeds)
        if prompt is not None:
            payload["prompt"] = prompt
        data = unwrap(self._http.post("/blog/keywords/suggest", payload))
        found = data.get("seeds") if isinstance(data, dict) else None
        return [str(seed) for seed in found] if isinstance(found, builtins.list) else []

    def plan_keywords(
        self, workspace_id: str, *, seeds: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Queue a research run; results land as ``suggested`` keywords.

        The calendar is untouched: setting a keyword's status to ``planned`` picks
        it. Follow the run in ``plan_run`` on the settings.
        """
        payload: dict[str, Any] = {"workspaceId": workspace_id}
        if seeds is not None:
            payload["seeds"] = builtins.list(seeds)
        data = unwrap(self._http.post("/blog/keywords/plan", payload))
        return data if isinstance(data, dict) else {"status": data}

    def add_keyword(
        self, workspace_id: str, *, keyword: str, planned_for: str | None = None
    ) -> BlogKeyword:
        payload: dict[str, Any] = {"workspaceId": workspace_id, "keyword": keyword}
        if planned_for is not None:
            payload["plannedFor"] = planned_for
        return BlogKeyword.model_validate(unwrap(self._http.post("/blog/keywords", payload)))

    def update_keyword(
        self,
        workspace_id: str,
        keyword_id: str,
        *,
        status: str | Any = UNSET,
        planned_for: str | None | Any = UNSET,
    ) -> BlogKeyword:
        """Setting ``status`` to ``planned`` picks the keyword; it takes the next free date."""
        body = self._http.request(
            "PATCH",
            f"/blog/keywords/{keyword_id}",
            json=_camel_body({"status": status, "planned_for": planned_for}),
            params={"workspace_id": workspace_id},
        )
        return BlogKeyword.model_validate(unwrap(body))

    def delete_keyword(self, workspace_id: str, keyword_id: str) -> None:
        self._http.request(
            "DELETE", f"/blog/keywords/{keyword_id}", params={"workspace_id": workspace_id}
        )

    # ── Articles ──────────────────────────────────────────────────

    def list_articles(
        self,
        workspace_id: str,
        *,
        status: str | Sequence[str] | None = None,
        limit: int | None = None,
    ) -> builtins.list[BlogArticle]:
        body = self._http.get(
            "/blog/articles",
            {"workspace_id": workspace_id, "status": _statuses(status), "limit": limit},
        )
        return parse_list(BlogArticle, unwrap(body))

    def request_article(
        self,
        workspace_id: str,
        *,
        title: str | None = None,
        keyword: str | None = None,
        keyword_id: str | None = None,
        instructions: str | None = None,
    ) -> BlogArticle:
        """Queue an article. One of ``title``, ``keyword`` or ``keyword_id`` is required."""
        payload: dict[str, Any] = {"workspaceId": workspace_id}
        for key, value in (
            ("title", title),
            ("keyword", keyword),
            ("keywordId", keyword_id),
            ("instructions", instructions),
        ):
            if value is not None:
                payload[key] = value
        return BlogArticle.model_validate(unwrap(self._http.post("/blog/articles", payload)))

    def get_article(self, workspace_id: str, article_id: str) -> BlogArticleFull:
        body = self._http.get(f"/blog/articles/{article_id}", {"workspace_id": workspace_id})
        return BlogArticleFull.model_validate(unwrap(body))

    def update_article(
        self,
        workspace_id: str,
        article_id: str,
        *,
        title: str | Any = UNSET,
        slug: str | Any = UNSET,
        excerpt: str | None | Any = UNSET,
        meta_title: str | None | Any = UNSET,
        meta_description: str | None | Any = UNSET,
        body_markdown: str | Any = UNSET,
        tags: Sequence[str] | Any = UNSET,
        publish_at: str | None | Any = UNSET,
    ) -> BlogArticleFull:
        """Edit an article.

        ``publish_at`` approves an article in review and puts it on the calendar;
        ``None`` returns it to review. A draft answers 409 until it is submitted.
        """
        body = self._http.request(
            "PATCH",
            f"/blog/articles/{article_id}",
            json=_camel_body(
                {
                    "title": title,
                    "slug": slug,
                    "excerpt": excerpt,
                    "meta_title": meta_title,
                    "meta_description": meta_description,
                    "body_markdown": body_markdown,
                    "tags": builtins.list(tags) if tags is not UNSET else UNSET,
                    "publish_at": publish_at,
                }
            ),
            params={"workspace_id": workspace_id},
        )
        return BlogArticleFull.model_validate(unwrap(body))

    def regenerate_article(self, workspace_id: str, article_id: str) -> BlogArticle:
        return self._article_action(workspace_id, article_id, "regenerate")

    def submit_article(self, workspace_id: str, article_id: str) -> BlogArticle:
        """Move a draft, failed or rejected article to ``in_review``; any other state is a 409."""
        return self._article_action(workspace_id, article_id, "submit")

    def publish_article(self, workspace_id: str, article_id: str) -> BlogArticle:
        """Publish an article in review now.

        A draft is a 409 until it is submitted; a 409 ``no_target`` means the
        workspace has no target set.
        """
        return self._article_action(workspace_id, article_id, "publish")

    def reject_article(self, workspace_id: str, article_id: str) -> BlogArticle:
        return self._article_action(workspace_id, article_id, "reject")

    def delete_article(self, workspace_id: str, article_id: str) -> None:
        self._http.request(
            "DELETE", f"/blog/articles/{article_id}", params={"workspace_id": workspace_id}
        )

    def _article_action(self, workspace_id: str, article_id: str, action: str) -> BlogArticle:
        body = self._http.request(
            "POST", f"/blog/articles/{article_id}/{action}", params={"workspace_id": workspace_id}
        )
        return BlogArticle.model_validate(unwrap(body))
