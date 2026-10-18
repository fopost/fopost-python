"""``client.queue`` — the posting queue: weekly slots and the next free times."""

from __future__ import annotations

import builtins
from datetime import datetime
from typing import Any

from .._http import unwrap
from ..models import QueueNext, QueueSlot, QueueSlotDeletion, QueueSlotUpdate
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["QueueResource"]


class QueueResource(Resource):
    def list_slots(self, *, workspace_id: str) -> builtins.list[QueueSlot]:
        """The recurring weekly slots of a workspace, ordered by weekday and time."""
        return parse_list(
            QueueSlot, unwrap(self._http.get("/queue/slots", {"workspace_id": workspace_id}))
        )

    def create_slot(
        self,
        *,
        workspace_id: str,
        weekday: int,
        time: str,
        timezone: str,
        account_id: str | None = None,
    ) -> QueueSlot:
        """Add a weekly slot. Omit ``account_id`` for one every account shares."""
        body: dict[str, Any] = {
            "workspace_id": workspace_id,
            "weekday": weekday,
            "time": time,
            "timezone": timezone,
        }
        if account_id is not None:
            body["account_id"] = account_id
        return QueueSlot.model_validate(unwrap(self._http.post("/queue/slots", body)))

    def update_slot(
        self,
        slot_id: str,
        *,
        account_id: str | None | Any = UNSET,
        weekday: int | Any = UNSET,
        time: str | Any = UNSET,
        timezone: str | Any = UNSET,
    ) -> QueueSlotUpdate:
        """Change a slot. Queued posts that no longer fit are moved and listed in ``moved``."""
        body = drop_unset(
            {"account_id": account_id, "weekday": weekday, "time": time, "timezone": timezone}
        )
        return QueueSlotUpdate.model_validate(
            unwrap(self._http.put(f"/queue/slots/{slot_id}", body))
        )

    def delete_slot(self, slot_id: str) -> QueueSlotDeletion:
        """Remove a slot. Posts that sat on it move to the next free occurrence."""
        return QueueSlotDeletion.model_validate(
            unwrap(self._http.delete(f"/queue/slots/{slot_id}"))
        )

    def next(self, *, workspace_id: str, account_id: str | None = None) -> datetime | None:
        """The time a post added to the queue now would get, or ``None`` with no slots."""
        body = self._http.get(
            "/queue/next", {"workspace_id": workspace_id, "account_id": account_id}
        )
        return QueueNext.model_validate(unwrap(body)).next

    def preview(
        self, *, workspace_id: str, account_id: str | None = None, count: int | None = None
    ) -> builtins.list[datetime]:
        """The next free occurrences in order, one per post that would be queued."""
        body = self._http.get(
            "/queue/preview",
            {"workspace_id": workspace_id, "account_id": account_id, "count": count},
        )
        data = unwrap(body)
        if not isinstance(data, list):
            return []
        return [datetime.fromisoformat(str(item).replace("Z", "+00:00")) for item in data]
