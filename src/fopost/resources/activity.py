"""``client.activity`` — what happened in a workspace, and the audit log."""

from __future__ import annotations

from datetime import datetime

from ..models import ActivityEvent, ActivityKind, ActivityPage
from ._base import Resource

__all__ = ["ActivityResource"]


def _when(value: datetime | str | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


class ActivityResource(Resource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        kind: ActivityKind | None = None,
        from_: datetime | str | None = None,
        to: datetime | str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ActivityPage:
        """Newest first. Omit ``workspace_id`` to read every workspace the key can reach.

        ``kind="security"`` is the audit log: members joining, leaving or changing
        role and access, and changes to two-step verification, passkeys, single
        sign-on and signed-in devices. Those rows are append-only and never expire.
        """
        body = self._http.get(
            "/activity",
            {
                "workspace_id": workspace_id,
                "kind": kind,
                "from": _when(from_),
                "to": _when(to),
                "cursor": cursor,
                "limit": limit,
            },
        )
        data = body.get("data") if isinstance(body, dict) else None
        meta = body.get("meta") if isinstance(body, dict) else None
        items = [ActivityEvent.model_validate(row) for row in data or []]
        next_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None
        return ActivityPage(items=items, next_cursor=next_cursor)
