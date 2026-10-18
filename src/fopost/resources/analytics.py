"""``client.analytics`` — deeper posting analytics.

Derived from the repeated readings the platform collector takes of every post
as it ages, so nothing here needs a second collection pass to be useful.
Every call needs the ``analytics`` scope.
"""

from __future__ import annotations

from urllib.parse import quote

from .._http import unwrap
from ..models import (
    AnalyticsCollectResult,
    AnalyticsOverview,
    AnalyticsTimeSeries,
    AudienceDemographics,
    AutomationPageMeta,
    CollectPostResult,
    ContentDecay,
    InboxAnalytics,
    LabelAnalytics,
    MetricChangePage,
    NativePost,
    Page,
    PageMeta,
    PostingFrequency,
    PostingStreakDay,
    PostsTable,
    PostsTableRow,
    PostsTableSummary,
    PostTimeline,
    TopPost,
)
from ._base import Resource, parse_list

__all__ = ["AnalyticsResource"]


class AnalyticsResource(Resource):
    def overview(
        self,
        *,
        days: int | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> AnalyticsOverview:
        """Dashboard totals, period deltas, today's stats and a per-account breakdown."""
        body = self._http.get(
            "/analytics/overview",
            {"days": days, "workspace_id": workspace_id, "account_id": account_id},
        )
        return AnalyticsOverview.model_validate(unwrap(body))

    def time_series(
        self,
        *,
        days: int | None = None,
        from_: str | None = None,
        to: str | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> AnalyticsTimeSeries:
        """Daily engagement, follower and post counts. Use ``days`` or ``from_``/``to``."""
        body = self._http.get(
            "/analytics/time-series",
            {
                "days": days,
                "from": from_,
                "to": to,
                "workspace_id": workspace_id,
                "account_id": account_id,
            },
        )
        return AnalyticsTimeSeries.model_validate(unwrap(body))

    def top_posts(
        self,
        *,
        limit: int | None = None,
        days: int | None = None,
        from_: str | None = None,
        to: str | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
        sort: str | None = None,
        label: str | None = None,
    ) -> list[TopPost]:
        """Posts ranked by engagement, or newest first with ``sort="recent"``."""
        body = self._http.get(
            "/analytics/top-posts",
            {
                "limit": limit,
                "days": days,
                "from": from_,
                "to": to,
                "workspace_id": workspace_id,
                "account_id": account_id,
                "sort": sort,
                "label": label,
            },
        )
        return parse_list(TopPost, unwrap(body))

    def labels(
        self,
        *,
        days: int | None = None,
        from_: str | None = None,
        to: str | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> list[LabelAnalytics]:
        """Post metrics rolled up per label, ranked by engagement."""
        body = self._http.get(
            "/analytics/labels",
            {
                "days": days,
                "from": from_,
                "to": to,
                "workspace_id": workspace_id,
                "account_id": account_id,
            },
        )
        return parse_list(LabelAnalytics, unwrap(body))

    def posts_table(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        days: int | None = None,
        from_: str | None = None,
        to: str | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> PostsTable:
        """Paginated posts of every status with per-delivery outcomes."""
        body = self._http.get(
            "/analytics/posts-table",
            {
                "page": page,
                "per_page": per_page,
                "days": days,
                "from": from_,
                "to": to,
                "workspace_id": workspace_id,
                "account_id": account_id,
            },
        )
        raw_meta = body.get("meta") if isinstance(body, dict) else None
        raw_summary = body.get("summary") if isinstance(body, dict) else None
        return PostsTable(
            items=parse_list(PostsTableRow, unwrap(body)),
            meta=AutomationPageMeta.model_validate(raw_meta)
            if isinstance(raw_meta, dict)
            else AutomationPageMeta(),
            summary=PostsTableSummary.model_validate(raw_summary)
            if isinstance(raw_summary, dict)
            else None,
        )

    def posting_streak(self, *, workspace_id: str | None = None) -> list[PostingStreakDay]:
        """365 days of posting activity, one row per day."""
        body = self._http.get("/analytics/posting-streak", {"workspace_id": workspace_id})
        data = unwrap(body)
        if isinstance(data, dict):
            data = data.get("streak")
        return parse_list(PostingStreakDay, data)

    def demographics(
        self,
        *,
        audience: str | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> AudienceDemographics:
        """Age, gender, country and city splits. ``audience`` is followers, engaged or reached."""
        body = self._http.get(
            "/analytics/demographics",
            {"audience": audience, "workspace_id": workspace_id, "account_id": account_id},
        )
        return AudienceDemographics.model_validate(unwrap(body))

    def inbox(
        self,
        *,
        days: int | None = None,
        tz: str | None = None,
        workspace_id: str | None = None,
        account_id: str | None = None,
    ) -> InboxAnalytics:
        """How the social inbox performed over the period. Aggregates only."""
        body = self._http.get(
            "/analytics/inbox",
            {"days": days, "tz": tz, "workspace_id": workspace_id, "account_id": account_id},
        )
        return InboxAnalytics.model_validate(unwrap(body))

    def collect(
        self, *, workspace_id: str | None = None, account_id: str | None = None
    ) -> AnalyticsCollectResult:
        """Collect fresh metrics now. Throttled per user; a 429 carries ``retry_after``."""
        body = self._http.request(
            "POST",
            "/analytics/collect",
            params={"workspace_id": workspace_id, "account_id": account_id},
        )
        return AnalyticsCollectResult.model_validate(unwrap(body))

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
