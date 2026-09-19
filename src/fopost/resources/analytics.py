"""``client.analytics`` — deeper posting analytics.

Derived from the repeated readings the platform collector takes of every post
as it ages, so nothing here needs a second collection pass to be useful.
Every call needs the ``analytics`` scope.
"""

from __future__ import annotations

from urllib.parse import quote

from .._http import unwrap
from ..models import (
    CollectPostResult,
    ContentDecay,
    MetricChangePage,
    NativePost,
    Page,
    PageMeta,
    PostingFrequency,
    PostTimeline,
)
from ._base import Resource, parse_list

__all__ = ["AnalyticsResource"]


class AnalyticsResource(Resource):
    def decay(
        self,
        *,
        days: int | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> ContentDecay:
        """How engagement accumulates with a post's age, and where the half-life falls.

        ``days`` selects posts by publish time, not reading time.
        """
        body = self._http.get(
            "/analytics/decay",
            {"days": days, "workspace_id": workspace_id, "accountId": account_id},
        )
        return ContentDecay.model_validate(unwrap(body))

    def frequency(
        self,
        *,
        days: int | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> PostingFrequency:
        """Weekly posting cadence set against what each cadence earned per post."""
        body = self._http.get(
            "/analytics/frequency",
            {"days": days, "workspace_id": workspace_id, "accountId": account_id},
        )
        return PostingFrequency.model_validate(unwrap(body))

    def timeline(self, id_or_permalink: str) -> PostTimeline:
        """Every reading held for one post, oldest first, one timeline per delivery.

        ``id_or_permalink`` is a FoPost post id or the permalink of a post made
        natively on the network.
        """
        path = f"/analytics/posts/{quote(id_or_permalink, safe='')}/timeline"
        return PostTimeline.model_validate(unwrap(self._http.get(path)))

    def changes(
        self,
        *,
        since: str | None = None,
        limit: int | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> MetricChangePage:
        """Readings recorded after ``since``, oldest first, with a cursor to continue.

        Poll this to mirror the metrics into your own store. Omitting ``since``
        gives the last seven days.
        """
        body = self._http.get(
            "/analytics/changes",
            {
                "since": since,
                "limit": limit,
                "workspace_id": workspace_id,
                "accountId": account_id,
            },
        )
        return MetricChangePage.model_validate(unwrap(body))

    def collect_post(self, id_or_permalink: str) -> CollectPostResult:
        """Re-read one post from the network now.

        Spends the same per-user budget as a full collection run, so a burst
        answers 429 with ``retryAfter``.
        """
        path = f"/posts/{quote(id_or_permalink, safe='')}/analytics/collect"
        return CollectPostResult.model_validate(unwrap(self._http.post(path)))

    def native_posts(
        self,
        account_id: str,
        *,
        page: int = 1,
        per_page: int = 20,
        days: int | None = None,
    ) -> Page[NativePost]:
        """Posts on the account that never went out through FoPost, newest first."""
        body = self._http.get(
            f"/accounts/{account_id}/native-posts",
            {"page": page, "per_page": per_page, "days": days},
        )
        items = parse_list(NativePost, body.get("data") if isinstance(body, dict) else body)
        raw_meta = body.get("meta") if isinstance(body, dict) else None
        meta = PageMeta.model_validate(raw_meta) if isinstance(raw_meta, dict) else PageMeta()
        return Page[NativePost](items=items, meta=meta)
