"""``fopost.chat_adapter``: the FoPost social inbox as a send/receive interface.

Wraps the inbox conversation and reply endpoints so a chatbot framework can treat
FoPost as one channel across every network that carries direct messages::

    from fopost import Fopost
    from fopost.chat_adapter import ChatAdapter

    chat = ChatAdapter(Fopost(), workspace_id=..., webhook_secret=...)

    event = chat.parse_webhook(raw_body, request.headers)   # inbound
    message = chat.receive_one(event)
    if message:
        chat.send(reply_to=message.id, text="On it.")       # outbound
"""

from __future__ import annotations

import builtins
import hashlib
import hmac
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .client import Fopost
from .models import InboxAttachment, InboxItem

__all__ = [
    "INBOUND_EVENT",
    "SIGNATURE_TOLERANCE_SECONDS",
    "ChatAdapter",
    "ChatAdapterError",
    "ChatAuthor",
    "ChatEvent",
    "ChatMessage",
    "to_chat_message",
]

#: The webhook event a new direct message raises.
INBOUND_EVENT = "inbox.message_received"

#: Refuse a delivery signed longer ago than this. Matches the API's own tolerance.
SIGNATURE_TOLERANCE_SECONDS = 300

_SIGNATURE_HEADER = "x-fopost-signature"
_TIMESTAMPED_SIGNATURE_HEADER = "x-fopost-signature-256"
_TIMESTAMP_HEADER = "x-fopost-timestamp"
_EVENT_HEADER = "x-fopost-event"


class ChatAdapterError(Exception):
    """A delivery that could not be trusted, or a target that cannot be reached.

    ``code`` is one of ``invalid_body``, ``unexpected_event``, ``missing_secret``,
    ``invalid_signature``, ``stale_delivery`` or ``unsupported_target``.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ChatAuthor:
    name: str | None = None
    handle: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class ChatMessage:
    """One inbound or outbound message, flattened out of an inbox item."""

    id: str
    conversation_id: str | None
    account_id: str | None
    platform: str
    type: str
    direction: str
    text: str
    author: ChatAuthor
    received_at: str | None
    can_reply: bool
    attachments: builtins.list[InboxAttachment] = field(default_factory=list)
    #: The untouched inbox item, for anything this shape drops.
    raw: InboxItem | None = None


@dataclass(frozen=True)
class ChatEvent:
    """A verified webhook delivery. Ids only: the text lives behind the API."""

    event: str
    item_id: str
    type: str
    platform: str
    account_id: str
    received_at: str | None = None
    #: When the API built the envelope, not when it was signed.
    timestamp: str | None = None


def to_chat_message(item: InboxItem) -> ChatMessage:
    received = item.platform_created_at or item.created_at
    return ChatMessage(
        id=item.id,
        conversation_id=item.conversation_id,
        account_id=item.account.id if item.account else None,
        platform=item.platform,
        type=item.type,
        direction=item.direction or "inbound",
        text=item.text or "",
        author=ChatAuthor(
            name=item.author_name,
            handle=item.author_handle,
            avatar_url=item.author_avatar_url,
        ),
        received_at=received.isoformat() if received is not None else None,
        can_reply=bool(item.can_reply),
        attachments=list(item.attachments),
        raw=item,
    )


def _header(headers: Mapping[str, Any], name: str) -> str | None:
    getter = getattr(headers, "get", None)
    if getter is not None:
        value = getter(name)
        if value is None:
            value = getter(name.title())
        if value is not None:
            return value[0] if isinstance(value, (list, tuple)) else str(value)
    for key, value in dict(headers).items():
        if key.lower() == name:
            return value[0] if isinstance(value, (list, tuple)) else str(value)
    return None


def _digest(value: str | None) -> str | None:
    if value is None:
        return None
    return value[7:] if value.startswith("sha256=") else value


class ChatAdapter:
    """Send and receive direct messages through one FoPost workspace."""

    def __init__(
        self,
        client: Fopost,
        *,
        workspace_id: str | None = None,
        webhook_secret: str | None = None,
        page_size: int = 25,
        lookback_pages: int = 4,
    ) -> None:
        self._client = client
        self._workspace_id = workspace_id
        self._webhook_secret = webhook_secret
        self._page_size = page_size
        self._lookback_pages = lookback_pages

    # ── Inbound ──

    def parse_webhook(self, body: str | bytes, headers: Mapping[str, Any]) -> ChatEvent:
        """Verify the delivery and return the event.

        Prefers the replay-safe ``X-FoPost-Signature-256`` and falls back to
        ``X-FoPost-Signature``. Pass the raw body, never a re-serialized object.
        """
        raw = body.decode() if isinstance(body, bytes) else body
        self.verify_webhook(raw, headers)

        try:
            envelope = json.loads(raw)
        except ValueError as err:
            raise ChatAdapterError("invalid_body", "Webhook body is not JSON") from err
        if not isinstance(envelope, dict):
            raise ChatAdapterError("invalid_body", "Webhook body is not an object")

        event = envelope.get("event") or _header(headers, _EVENT_HEADER)
        if event != INBOUND_EVENT:
            raise ChatAdapterError(
                "unexpected_event", f"Expected {INBOUND_EVENT}, got {event or 'nothing'}"
            )

        data = envelope.get("data") or {}
        item_id, account_id = data.get("itemId"), data.get("accountId")
        if not isinstance(item_id, str) or not isinstance(account_id, str):
            raise ChatAdapterError("invalid_body", "Webhook payload carries no item id")

        return ChatEvent(
            event=event,
            item_id=item_id,
            type=data.get("type") or "dm",
            platform=data.get("platform") or "",
            account_id=account_id,
            received_at=data.get("receivedAt"),
            timestamp=envelope.get("timestamp"),
        )

    def verify_webhook(self, body: str | bytes, headers: Mapping[str, Any]) -> None:
        """Raise ``ChatAdapterError`` when the delivery is unsigned, forged or stale."""
        if not self._webhook_secret:
            raise ChatAdapterError("missing_secret", "Pass webhook_secret to verify a delivery")

        raw = body.encode() if isinstance(body, str) else body
        secret = self._webhook_secret.encode()

        timestamped = _digest(_header(headers, _TIMESTAMPED_SIGNATURE_HEADER))
        if timestamped is not None:
            try:
                sent_at = int(_header(headers, _TIMESTAMP_HEADER) or "")
            except ValueError as err:
                raise ChatAdapterError(
                    "invalid_signature", "Signed delivery carries no timestamp"
                ) from err
            age = abs(time.time() - sent_at)
            if age > SIGNATURE_TOLERANCE_SECONDS:
                raise ChatAdapterError("stale_delivery", f"Delivery is {int(age)}s old")
            expected = hmac.new(secret, f"{sent_at}.".encode() + raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(timestamped, expected):
                raise ChatAdapterError("invalid_signature", "Signature does not match the body")
            return

        plain = _digest(_header(headers, _SIGNATURE_HEADER))
        if plain is None:
            raise ChatAdapterError("invalid_signature", "Delivery carries no signature header")
        if not hmac.compare_digest(plain, hmac.new(secret, raw, hashlib.sha256).hexdigest()):
            raise ChatAdapterError("invalid_signature", "Signature does not match the body")

    def receive(
        self,
        *,
        account_id: str | None = None,
        conversation_id: str | None = None,
        platform: str | None = None,
        state: str | None = "unread",
        limit: int | None = None,
    ) -> builtins.list[ChatMessage]:
        """Inbound direct messages, newest first. Unread by default.

        Pass ``state=None`` to read every state.
        """
        page = self._client.inbox.list(
            workspace_id=self._workspace_id,
            type="dm",
            direction="inbound",
            state=state,
            account_id=account_id,
            conversation_id=conversation_id,
            platform=platform,
            per_page=limit or self._page_size,
        )
        return [to_chat_message(item) for item in page.items]

    def receive_one(self, ref: str | ChatEvent) -> ChatMessage | None:
        """The message behind a webhook event, or an item id.

        The event carries ids only, so this reads the text back through the inbox.
        It scans ``lookback_pages`` of that account's items and answers ``None``
        when the item has aged past them or was deleted.
        """
        item_id = ref if isinstance(ref, str) else ref.item_id
        narrow: dict[str, Any] = (
            {} if isinstance(ref, str) else {"account_id": ref.account_id, "type": ref.type}
        )

        for page_number in range(1, self._lookback_pages + 1):
            page = self._client.inbox.list(
                workspace_id=self._workspace_id,
                page=page_number,
                per_page=self._page_size,
                **narrow,
            )
            for item in page.items:
                if item.id == item_id:
                    return to_chat_message(item)
            if len(page.items) < self._page_size:
                return None
        return None

    # ── Outbound ──

    def send(
        self,
        *,
        reply_to: str | None = None,
        conversation_id: str | None = None,
        account_id: str | None = None,
        handle: str | None = None,
        text: str | None = None,
        media_ids: Sequence[str] | None = None,
        quick_replies: Sequence[str] | None = None,
    ) -> ChatMessage:
        """Send on the platform as the connected account. Needs the ``publish`` scope.

        One of three shapes: ``reply_to`` a message, ``conversation_id`` to reply
        into a thread, or ``account_id`` plus ``handle`` to open one.
        """
        media = list(media_ids) if media_ids is not None else None
        quick = list(quick_replies) if quick_replies is not None else None

        if reply_to is not None:
            result = self._client.inbox.reply(reply_to, text, media_ids=media, quick_replies=quick)
            return to_chat_message(result.item)

        if conversation_id is not None:
            latest = self._latest_in(conversation_id)
            if latest is None:
                raise ChatAdapterError(
                    "unsupported_target",
                    f"Conversation {conversation_id} has no message to reply to",
                )
            result = self._client.inbox.reply(latest.id, text, media_ids=media, quick_replies=quick)
            return to_chat_message(result.item)

        if account_id is None or handle is None or text is None:
            raise ChatAdapterError(
                "unsupported_target",
                "Pass reply_to, conversation_id, or account_id with handle and text",
            )

        started = self._client.inbox.start_conversation(
            text=text, account_id=account_id, handle=handle, media_ids=media
        )
        if started.item is None:
            raise ChatAdapterError(
                "unsupported_target", f"{handle} accepted the message but returned no item"
            )
        return to_chat_message(started.item)

    def typing(self, conversation_id: str, account_id: str, on: bool = True) -> None:
        """Show (default) or clear the typing indicator. Needs the ``publish`` scope."""
        self._client.inbox.set_typing(conversation_id, account_id=account_id, on=on)

    def mark_read(self, message: ChatMessage | str) -> None:
        """Mark one message read, so ``receive()`` stops returning it."""
        item_id = message if isinstance(message, str) else message.id
        self._client.inbox.update(item_id, state="read")

    # ── Internals ──

    def _latest_in(self, conversation_id: str) -> InboxItem | None:
        page = self._client.inbox.list(
            workspace_id=self._workspace_id,
            conversation_id=conversation_id,
            sort="newest",
            per_page=1,
        )
        return page.items[0] if page.items else None
