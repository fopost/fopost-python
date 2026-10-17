"""``client.broadcasts`` and ``client.sequences`` — one message into many
conversations, and a series of messages on a delay.

Neither opens a cold DM: every message lands in a direct-message thread the
contact already started. Both honour each network's messaging window
server-side. Messenger and Instagram take a business-initiated message only
within 24 hours of the contact's last one, so a recipient outside it comes
back ``skipped`` with ``skip_reason="window_closed"`` and nothing is
attempted — which is why the number sent is often lower than the audience.
Telegram, Slack, Bluesky and Reddit have no window.
"""

from __future__ import annotations

import builtins
from typing import Any, TypeVar

from .._http import unwrap
from ..models import (
    AudienceFilter,
    Broadcast,
    BroadcastRecipient,
    Enrollment,
    FopostModel,
    Page,
    PageMeta,
    Sequence,
    SequenceStep,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["BroadcastsResource", "SequencesResource"]


def _audience(audience: AudienceFilter | dict[str, Any] | None) -> dict[str, Any] | None:
    if audience is None:
        return None
    return (
        audience.model_dump(exclude_none=True) if isinstance(audience, AudienceFilter) else audience
    )


def _steps(
    steps: builtins.list[SequenceStep] | builtins.list[dict[str, Any]],
) -> builtins.list[dict[str, Any]]:
    return [s.model_dump(exclude_none=True) if isinstance(s, SequenceStep) else s for s in steps]


T = TypeVar("T", bound=FopostModel)


def _page(model: type[T], body: Any, per_page: int) -> Page[T]:
    items: builtins.list[T] = parse_list(
        model, body.get("data") if isinstance(body, dict) else body
    )
    raw = body.get("pagination") if isinstance(body, dict) else None
    meta = PageMeta.model_validate(raw) if isinstance(raw, dict) else PageMeta(per_page=per_page)
    return Page[model](items=items, meta=meta)  # type: ignore[valid-type]


class BroadcastsResource(Resource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[Broadcast]:
        """One page of broadcasts, newest first.

        Omit ``workspace_id`` to span every workspace the key can reach; each
        broadcast then carries ``workspace_id``.
        """
        body = self._http.get(
            "/broadcasts",
            {
                "workspace_id": workspace_id,
                "status": status,
                "page": page,
                "per_page": per_page,
            },
        )
        return _page(Broadcast, body, per_page)

    def get(self, broadcast_id: str) -> Broadcast:
        return Broadcast.model_validate(unwrap(self._http.get(f"/broadcasts/{broadcast_id}")))

    def create(
        self,
        *,
        workspace_id: str,
        account_id: str,
        name: str,
        text: str,
        media_id: str | None = None,
        audience: AudienceFilter | dict[str, Any] | None = None,
        scheduled_at: str | None = None,
    ) -> Broadcast:
        """Create it without sending.

        Give ``scheduled_at`` to have it go out on its own at that time;
        otherwise call :meth:`send`. ``audience`` omitted means every contact
        in the workspace.
        """
        payload: dict[str, Any] = {
            "workspace_id": workspace_id,
            "account_id": account_id,
            "name": name,
            "text": text,
        }
        if media_id is not None:
            payload["media_id"] = media_id
        if audience is not None:
            payload["audience"] = _audience(audience)
        if scheduled_at is not None:
            payload["scheduled_at"] = scheduled_at
        return Broadcast.model_validate(unwrap(self._http.post("/broadcasts", payload)))

    def update(
        self,
        broadcast_id: str,
        *,
        name: str | None | Any = UNSET,
        text: str | None | Any = UNSET,
        media_id: str | None | Any = UNSET,
        audience: AudienceFilter | dict[str, Any] | Any = UNSET,
        scheduled_at: str | None | Any = UNSET,
    ) -> Broadcast:
        """Only a draft or scheduled broadcast can be edited."""
        payload = drop_unset(
            {
                "name": name,
                "text": text,
                "media_id": media_id,
                "audience": _audience(audience) if audience is not UNSET else UNSET,
                "scheduled_at": scheduled_at,
            }
        )
        return Broadcast.model_validate(
            unwrap(self._http.request("PATCH", f"/broadcasts/{broadcast_id}", json=payload))
        )

    def send(self, broadcast_id: str) -> dict[str, Any]:
        """Freeze the audience into a recipient list and start sending.

        The returned ``recipients`` is how many contacts matched, not how many
        will be messaged — the messaging window decides that. Needs the
        ``publish`` scope as well as ``inbox``.
        """
        result: dict[str, Any] = unwrap(self._http.post(f"/broadcasts/{broadcast_id}/send", {}))
        return result

    def cancel(self, broadcast_id: str) -> dict[str, Any]:
        """Stop it where it stands.

        Anyone not yet written to stays unsent; messages already delivered are
        not recalled. Needs the ``publish`` scope as well as ``inbox``.
        """
        result: dict[str, Any] = unwrap(self._http.post(f"/broadcasts/{broadcast_id}/cancel", {}))
        return result

    def recipients(
        self,
        broadcast_id: str,
        *,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Page[BroadcastRecipient]:
        """One row per contact, with what became of their message.

        A skipped row carries ``skip_reason``.
        """
        body = self._http.get(
            f"/broadcasts/{broadcast_id}/recipients",
            {"status": status, "page": page, "per_page": per_page},
        )
        return _page(BroadcastRecipient, body, per_page)

    def delete(self, broadcast_id: str) -> None:
        """Remove the broadcast and its recipient records.

        Messages already sent stay in the conversations they went to.
        """
        self._http.delete(f"/broadcasts/{broadcast_id}")


class SequencesResource(Resource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[Sequence]:
        body = self._http.get(
            "/sequences",
            {"workspace_id": workspace_id, "page": page, "per_page": per_page},
        )
        return _page(Sequence, body, per_page)

    def get(self, sequence_id: str) -> Sequence:
        return Sequence.model_validate(unwrap(self._http.get(f"/sequences/{sequence_id}")))

    def create(
        self,
        *,
        workspace_id: str,
        account_id: str,
        name: str,
        steps: builtins.list[SequenceStep] | builtins.list[dict[str, Any]],
        status: str | None = None,
    ) -> Sequence:
        """Creating a sequence enrolls nobody."""
        payload: dict[str, Any] = {
            "workspace_id": workspace_id,
            "account_id": account_id,
            "name": name,
            "steps": _steps(steps),
        }
        if status is not None:
            payload["status"] = status
        return Sequence.model_validate(unwrap(self._http.post("/sequences", payload)))

    def update(
        self,
        sequence_id: str,
        *,
        name: str | None | Any = UNSET,
        steps: builtins.list[SequenceStep] | builtins.list[dict[str, Any]] | Any = UNSET,
        status: str | None | Any = UNSET,
    ) -> Sequence:
        """Pausing stops every enrollment from firing without ending any of them."""
        payload = drop_unset(
            {
                "name": name,
                "steps": _steps(steps) if steps is not UNSET and steps is not None else steps,
                "status": status,
            }
        )
        return Sequence.model_validate(
            unwrap(self._http.request("PATCH", f"/sequences/{sequence_id}", json=payload))
        )

    def enroll(
        self,
        sequence_id: str,
        *,
        contact_ids: builtins.list[str] | None = None,
        audience: AudienceFilter | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Put contacts on the sequence, by id or by audience.

        Re-enrolling someone restarts their walk from the first step rather
        than running two in parallel. Needs the ``publish`` scope as well as
        ``inbox``.
        """
        payload: dict[str, Any] = {}
        if contact_ids is not None:
            payload["contact_ids"] = contact_ids
        if audience is not None:
            payload["audience"] = _audience(audience)
        result: dict[str, Any] = unwrap(
            self._http.post(f"/sequences/{sequence_id}/enroll", payload)
        )
        return result

    def unenroll(self, sequence_id: str, contact_ids: builtins.list[str]) -> dict[str, Any]:
        """Nothing further fires for them. Needs the ``publish`` scope."""
        result: dict[str, Any] = unwrap(
            self._http.post(f"/sequences/{sequence_id}/unenroll", {"contact_ids": contact_ids})
        )
        return result

    def enrollments(
        self,
        sequence_id: str,
        *,
        page: int = 1,
        per_page: int = 50,
    ) -> Page[Enrollment]:
        """Who is on it, what step they are at, and when the next one is due."""
        body = self._http.get(
            f"/sequences/{sequence_id}/enrollments",
            {"page": page, "per_page": per_page},
        )
        return _page(Enrollment, body, per_page)

    def delete(self, sequence_id: str) -> None:
        """Remove the sequence and every enrollment on it."""
        self._http.delete(f"/sequences/{sequence_id}")
