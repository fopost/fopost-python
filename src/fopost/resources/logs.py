"""``client.logs`` — recent API request activity, kept for 30 days."""

from __future__ import annotations

from .._http import unwrap
from ..models import RequestLog, RequestLogMeta, RequestLogPage, RequestLogSummary
from ._base import Resource, parse_list

__all__ = ["LogsResource"]


class LogsResource(Resource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        days: int | None = None,
        status: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
        platform: str | None = None,
        route: str | None = None,
        q: str | None = None,
        limit: int | None = None,
        before: int | None = None,
    ) -> RequestLogPage:
        """Request rows newest first. ``before`` is ``meta.next_cursor`` from the last page."""
        body = self._http.get(
            "/logs",
            {
                "workspace_id": workspace_id,
                "days": days,
                "status": status,
                "method": method,
                "status_code": status_code,
                "platform": platform,
                "route": route,
                "q": q,
                "limit": limit,
                "before": before,
            },
        )
        items = parse_list(RequestLog, unwrap(body))
        raw_meta = body.get("meta") if isinstance(body, dict) else None
        raw_summary = body.get("summary") if isinstance(body, dict) else None
        return RequestLogPage(
            items=items,
            meta=RequestLogMeta.model_validate(raw_meta)
            if isinstance(raw_meta, dict)
            else RequestLogMeta(),
            summary=RequestLogSummary.model_validate(raw_summary)
            if isinstance(raw_summary, dict)
            else None,
        )
