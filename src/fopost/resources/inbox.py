"""``client.inbox`` — comments, mentions and direct messages on connected accounts."""

from __future__ import annotations

import builtins
from typing import Any

from .._http import unwrap
from ..models import (
    InboxAccount,
    InboxApproval,
    InboxConversation,
    InboxHandover,
    InboxItem,
    InboxPlatform,
    InboxRefreshResult,
    InboxReplyResult,
    InboxStartConversationResult,
    InboxThread,
    Page,
    PageMeta,
)
from ._base import Resource, parse_list

__all__ = ["InboxResource"]


def _page(model: Any, body: Any) -> Any:
    items = parse_list(model, body.get("data") if isinstance(body, dict) else body)
    raw_meta = body.get("meta") if isinstance(body, dict) else None
    meta = PageMeta.model_validate(raw_meta) if isinstance(raw_meta, dict) else PageMeta()
    return Page[model](items=items, meta=meta)


class InboxResource(Resource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        type: str | None = None,
        state: str | None = None,
        platform: str | None = None,
        account_id: str | None = None,
        post_id: str | None = None,
        post_external_id: str | None = None,
        conversation_id: str | None = None,
        direction: str | None = None,
        q: str | None = None,
        sort: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[InboxItem]:
        """One page of items, newest first. ``meta.per_page`` and ``meta.total`` are set."""
        body = self._http.get(
            "/inbox",
            {
                "workspace_id": workspace_id,
                "type": type,
                "state": state,
                "platform": platform,
                "account_id": account_id,
                "post_id": post_id,
                "post_external_id": post_external_id,
                "conversation_id": conversation_id,
                "direction": direction,
                "q": q,
                "sort": sort,
                "page": page,
                "per_page": per_page,
            },
        )
        return _page(InboxItem, body)  # type: ignore[no-any-return]

    def threads(
        self,
        *,
        workspace_id: str | None = None,
        kind: str | None = None,
        platform: str | None = None,
        account_id: str | None = None,
        state: str | None = None,
        q: str | None = None,
        sort: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[InboxThread]:
        """One row per post with comments; ``kind="mentions"`` for posts we were tagged in."""
        body = self._http.get(
            "/inbox/posts",
            {
                "workspace_id": workspace_id,
                "kind": kind,
                "platform": platform,
                "account_id": account_id,
                "state": state,
                "q": q,
                "sort": sort,
                "page": page,
                "per_page": per_page,
            },
        )
        return _page(InboxThread, body)  # type: ignore[no-any-return]

    def conversations(
        self,
        *,
        workspace_id: str | None = None,
        platform: str | None = None,
        account_id: str | None = None,
        state: str | None = None,
        q: str | None = None,
        sort: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[InboxConversation]:
        """One row per DM thread, latest first."""
        body = self._http.get(
            "/inbox/conversations",
            {
                "workspace_id": workspace_id,
                "platform": platform,
                "account_id": account_id,
                "state": state,
                "q": q,
                "sort": sort,
                "page": page,
                "per_page": per_page,
            },
        )
        return _page(InboxConversation, body)  # type: ignore[no-any-return]

    def unread_count(self, *, workspace_id: str | None = None) -> int:
        body = self._http.get("/inbox/unread-count", {"workspace_id": workspace_id})
        count = body.get("count") if isinstance(body, dict) else None
        return int(count) if isinstance(count, int) else 0

    def accounts(self, *, workspace_id: str | None = None) -> builtins.list[InboxAccount]:
        """Every active account, flagged with whether comments and DMs can be read for it."""
        return parse_list(
            InboxAccount,
            unwrap(self._http.get("/inbox/accounts", {"workspace_id": workspace_id})),
        )

    def platforms(self) -> builtins.list[InboxPlatform]:
        return parse_list(InboxPlatform, unwrap(self._http.get("/inbox/platforms")))

    def mark_thread_read(
        self,
        *,
        workspace_id: str,
        account_id: str,
        post_external_id: str | None = None,
        conversation_id: str | None = None,
    ) -> int:
        """Read a whole comment thread or DM thread; returns how many items changed."""
        body: dict[str, Any] = {"workspace_id": workspace_id, "account_id": account_id}
        if post_external_id is not None:
            body["post_external_id"] = post_external_id
        if conversation_id is not None:
            body["conversation_id"] = conversation_id
        result = unwrap(self._http.post("/inbox/read", body))
        updated = result.get("updated") if isinstance(result, dict) else None
        return int(updated) if isinstance(updated, int) else 0

    def refresh(self, *, workspace_id: str) -> InboxRefreshResult:
        """Poll every inbox-capable account in the workspace now."""
        return InboxRefreshResult.model_validate(
            unwrap(self._http.post("/inbox/refresh", {"workspace_id": workspace_id}))
        )

    def update(self, item_id: str, *, state: str, snoozed_until: str | None = None) -> InboxItem:
        """Mark the item ``unread``, ``read``, ``resolved`` or ``snoozed``."""
        body: dict[str, Any] = {"state": state}
        if snoozed_until is not None:
            body["snoozedUntil"] = snoozed_until
        return InboxItem.model_validate(
            unwrap(self._http.request("PATCH", f"/inbox/{item_id}", json=body))
        )

    def edit_comment(self, item_id: str, text: str) -> InboxItem:
        """Edit our own comment on the platform, where ``can_edit`` is true."""
        return InboxItem.model_validate(
            unwrap(self._http.request("PATCH", f"/inbox/{item_id}", json={"text": text}))
        )

    def reply(
        self,
        item_id: str,
        text: str | None = None,
        *,
        media_ids: builtins.list[str] | None = None,
        quick_replies: builtins.list[str] | None = None,
    ) -> InboxReplyResult:
        """Send the reply on the platform as the connected account.

        ``text`` may be omitted when ``media_ids`` is given. ``media_ids`` and
        ``quick_replies`` apply to DMs and also need the ``publish`` scope.
        """
        body: dict[str, Any] = {}
        if text is not None:
            body["text"] = text
        if media_ids is not None:
            body["media_ids"] = media_ids
        if quick_replies is not None:
            body["quick_replies"] = quick_replies
        return InboxReplyResult.model_validate(
            unwrap(self._http.post(f"/inbox/{item_id}/reply", body))
        )

    def hide(self, item_id: str) -> InboxItem:
        return InboxItem.model_validate(unwrap(self._http.post(f"/inbox/{item_id}/hide")))

    def unhide(self, item_id: str) -> InboxItem:
        return InboxItem.model_validate(unwrap(self._http.post(f"/inbox/{item_id}/unhide")))

    def delete(self, item_id: str) -> None:
        """Delete the comment on the platform, including our own reply."""
        self._http.delete(f"/inbox/{item_id}")

    def like(self, item_id: str) -> InboxItem:
        """Like, upvote or favourite the item, where ``can_like`` is true."""
        return InboxItem.model_validate(unwrap(self._http.post(f"/inbox/{item_id}/like")))

    def unlike(self, item_id: str) -> InboxItem:
        return InboxItem.model_validate(unwrap(self._http.post(f"/inbox/{item_id}/unlike")))

    def pin(self, item_id: str) -> InboxItem:
        """Pin our own comment, where ``can_pin`` is true."""
        return InboxItem.model_validate(unwrap(self._http.post(f"/inbox/{item_id}/pin")))

    def unpin(self, item_id: str) -> InboxItem:
        return InboxItem.model_validate(unwrap(self._http.post(f"/inbox/{item_id}/unpin")))

    def react(self, item_id: str, reaction: str | None) -> InboxItem:
        """React to a message with an emoji, or ``None`` to remove ours."""
        return InboxItem.model_validate(
            unwrap(self._http.post(f"/inbox/{item_id}/react", {"reaction": reaction}))
        )

    def start_conversation(
        self,
        *,
        text: str,
        account_id: str | None = None,
        handle: str | None = None,
        comment_id: str | None = None,
        media_ids: builtins.list[str] | None = None,
    ) -> InboxStartConversationResult:
        """Open a DM to ``handle`` from ``account_id``, or privately answer ``comment_id``."""
        body: dict[str, Any] = {"text": text}
        if account_id is not None:
            body["account_id"] = account_id
        if handle is not None:
            body["handle"] = handle
        if comment_id is not None:
            body["comment_id"] = comment_id
        if media_ids is not None:
            body["media_ids"] = media_ids
        return InboxStartConversationResult.model_validate(
            unwrap(self._http.post("/inbox/conversations", body))
        )

    def set_typing(self, conversation_id: str, *, account_id: str, on: bool = True) -> bool:
        """Show or clear the typing indicator in a DM thread."""
        result = unwrap(
            self._http.post(
                f"/inbox/conversations/{conversation_id}/typing",
                {"account_id": account_id, "on": on},
            )
        )
        typing = result.get("typing") if isinstance(result, dict) else None
        return bool(typing)

    def handover(
        self,
        conversation_id: str,
        *,
        account_id: str,
        app_id: str | None = None,
        metadata: str | None = None,
    ) -> InboxHandover:
        """Pass a Messenger thread to another Meta app, or take it back without ``app_id``."""
        body: dict[str, Any] = {"account_id": account_id}
        if app_id is not None:
            body["app_id"] = app_id
        if metadata is not None:
            body["metadata"] = metadata
        return InboxHandover.model_validate(
            unwrap(self._http.post(f"/inbox/conversations/{conversation_id}/handover", body))
        )

    def list_approvals(self, *, workspace_id: str | None = None) -> builtins.list[InboxApproval]:
        """Replies an automation or the agent drafted that a person still has to send."""
        return parse_list(
            InboxApproval,
            unwrap(self._http.get("/inbox/approvals", {"workspace_id": workspace_id})),
        )

    def approve_reply(self, approval_id: int, *, text: str | None = None) -> dict[str, Any]:
        """Send the draft, or ``text`` in its place."""
        body = {"text": text} if text is not None else {}
        result = unwrap(self._http.post(f"/inbox/approvals/{approval_id}/approve", body))
        return result if isinstance(result, dict) else {"data": result}

    def reject_reply(self, approval_id: int) -> dict[str, Any]:
        result = unwrap(self._http.post(f"/inbox/approvals/{approval_id}/reject"))
        return result if isinstance(result, dict) else {"data": result}
