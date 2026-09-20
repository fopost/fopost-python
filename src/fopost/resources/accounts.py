"""``client.accounts`` — the social accounts connected to a workspace."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    AccountMove,
    AccountRename,
    DiscordChannel,
    DiscordIdentity,
    DiscordMember,
    DiscordMessage,
    DiscordMessageRef,
    DiscordRole,
    DiscordScheduledEvent,
    SlackChannel,
    SlackIdentity,
    SlackMember,
    SocialAccount,
    TelegramBotCommand,
    TelegramBotCommands,
    TelegramConnectCode,
    TelegramConnectStatus,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["AccountsResource"]


class AccountsResource(Resource):
    def list(
        self, *, workspace_id: str | None = None, group_id: str | None = None
    ) -> list[SocialAccount]:
        """Connected accounts, across every workspace unless one is named."""
        # This endpoint reads a camelCase workspaceId; posts and labels use snake.
        return parse_list(
            SocialAccount,
            unwrap(
                self._http.get("/accounts", {"workspaceId": workspace_id, "group_id": group_id})
            ),
        )

    def get(self, account_id: str) -> SocialAccount:
        return SocialAccount.model_validate(unwrap(self._http.get(f"/accounts/{account_id}")))

    def health(self, account_id: str) -> dict[str, Any]:
        """Token validity and last-check detail for one account."""
        body = unwrap(self._http.get(f"/accounts/{account_id}/health"))
        return body if isinstance(body, dict) else {"data": body}

    def update(self, account_id: str, *, display_name: str | None) -> AccountRename:
        """Rename the account; ``None`` or an empty string restores the platform name."""
        return AccountRename.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}", json={"display_name": display_name}
                )
            )
        )

    def move(self, account_id: str, *, workspace_id: str) -> AccountMove:
        """Move the account to another workspace the caller owns."""
        return AccountMove.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/move", {"workspace_id": workspace_id}))
        )

    def create_telegram_connect_code(
        self, *, workspace_id: str | None = None
    ) -> TelegramConnectCode:
        """Mint a one-time code; send ``/connect <code>`` to the bot in a chat to connect it."""
        body = {} if workspace_id is None else {"workspaceId": workspace_id}
        return TelegramConnectCode.model_validate(
            unwrap(self._http.post("/accounts/telegram/connect-code", body))
        )

    def get_telegram_connect_status(self, code: str) -> TelegramConnectStatus:
        return TelegramConnectStatus.model_validate(
            unwrap(self._http.get("/accounts/telegram/connect-code/status", {"code": code}))
        )

    def get_telegram_bot_commands(self, account_id: str) -> TelegramBotCommands:
        return TelegramBotCommands.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/telegram/commands"))
        )

    def set_telegram_bot_commands(
        self,
        account_id: str,
        commands: Sequence[TelegramBotCommand | Mapping[str, str]],
    ) -> TelegramBotCommands:
        """Replace the bot's command menu for this chat."""
        payload = [
            {"command": c.command, "description": c.description}
            if isinstance(c, TelegramBotCommand)
            else {"command": c["command"], "description": c["description"]}
            for c in commands
        ]
        return TelegramBotCommands.model_validate(
            unwrap(
                self._http.put(f"/accounts/{account_id}/telegram/commands", {"commands": payload})
            )
        )

    def delete_telegram_bot_commands(self, account_id: str) -> TelegramBotCommands:
        return TelegramBotCommands.model_validate(
            unwrap(self._http.delete(f"/accounts/{account_id}/telegram/commands"))
        )

    def list_slack_channels(self, account_id: str) -> builtins.list[SlackChannel]:
        """Channels the Slack app can post to in the connected workspace."""
        return parse_list(
            SlackChannel, unwrap(self._http.get(f"/accounts/{account_id}/slack/channels"))
        )

    def list_slack_members(self, account_id: str) -> builtins.list[SlackMember]:
        """People in the connected Slack workspace; a member ``id`` is a DM handle."""
        return parse_list(
            SlackMember, unwrap(self._http.get(f"/accounts/{account_id}/slack/members"))
        )

    def get_slack_identity(self, account_id: str) -> SlackIdentity:
        return SlackIdentity.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/slack/identity"))
        )

    def update_slack_identity(
        self,
        account_id: str,
        *,
        username: str | None | Any = UNSET,
        icon_url: str | None | Any = UNSET,
        icon_emoji: str | None | Any = UNSET,
    ) -> SlackIdentity:
        """Set the posting name and icon; omitted keeps a field, ``None`` clears it."""
        body = drop_unset({"username": username, "icon_url": icon_url, "icon_emoji": icon_emoji})
        return SlackIdentity.model_validate(
            unwrap(self._http.request("PATCH", f"/accounts/{account_id}/slack/identity", json=body))
        )

    # ── Discord (bot connections; a webhook one answers 409 webhook_connection) ──

    def list_discord_channels(self, account_id: str) -> builtins.list[DiscordChannel]:
        """Text channels the bot can post to in the connected server."""
        return parse_list(
            DiscordChannel, unwrap(self._http.get(f"/accounts/{account_id}/discord/channels"))
        )

    def switch_discord_channel(self, account_id: str, channel_id: str) -> DiscordChannel:
        """Move the account to another channel in the same server."""
        return DiscordChannel.model_validate(
            unwrap(
                self._http.request(
                    "PATCH",
                    f"/accounts/{account_id}/discord/channels/current",
                    json={"channel_id": channel_id},
                )
            )
        )

    def get_discord_identity(self, account_id: str) -> DiscordIdentity:
        return DiscordIdentity.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/discord/identity"))
        )

    def update_discord_identity(
        self,
        account_id: str,
        *,
        username: str | None | Any = UNSET,
        avatar_url: str | None | Any = UNSET,
    ) -> DiscordIdentity:
        """Set the bot's nickname and avatar; omitted keeps a field, ``None`` clears it."""
        body = drop_unset({"username": username, "avatar_url": avatar_url})
        return DiscordIdentity.model_validate(
            unwrap(
                self._http.request("PATCH", f"/accounts/{account_id}/discord/identity", json=body)
            )
        )

    def list_discord_pins(self, account_id: str) -> builtins.list[DiscordMessage]:
        return parse_list(
            DiscordMessage,
            unwrap(self._http.get(f"/accounts/{account_id}/discord/messages/pinned")),
        )

    def delete_discord_message(self, account_id: str, message_id: str) -> bool:
        data = unwrap(self._http.delete(f"/accounts/{account_id}/discord/messages/{message_id}"))
        return bool(data.get("deleted")) if isinstance(data, Mapping) else False

    def pin_discord_message(self, account_id: str, message_id: str) -> bool:
        data = unwrap(self._http.post(f"/accounts/{account_id}/discord/messages/{message_id}/pin"))
        return bool(data.get("pinned")) if isinstance(data, Mapping) else False

    def unpin_discord_message(self, account_id: str, message_id: str) -> bool:
        data = unwrap(
            self._http.delete(f"/accounts/{account_id}/discord/messages/{message_id}/pin")
        )
        return bool(data.get("pinned")) if isinstance(data, Mapping) else False

    def crosspost_discord_message(self, account_id: str, message_id: str) -> DiscordMessageRef:
        """Publish an announcement-channel message to every server following it."""
        return DiscordMessageRef.model_validate(
            unwrap(
                self._http.post(f"/accounts/{account_id}/discord/messages/{message_id}/crosspost")
            )
        )

    def create_discord_thread(
        self,
        account_id: str,
        message_id: str,
        *,
        name: str,
        auto_archive_duration: int | None = None,
    ) -> dict[str, Any]:
        """Start a thread on a message; the duration is 60, 1440, 4320 or 10080 minutes."""
        body: dict[str, Any] = {"name": name}
        if auto_archive_duration is not None:
            body["auto_archive_duration"] = auto_archive_duration
        data = unwrap(
            self._http.post(
                f"/accounts/{account_id}/discord/messages/{message_id}/thread", json=body
            )
        )
        return dict(data) if isinstance(data, Mapping) else {}

    def send_discord_dm(self, account_id: str, member_id: str, content: str) -> DiscordMessageRef:
        """Send one message to a member of the server."""
        return DiscordMessageRef.model_validate(
            unwrap(
                self._http.post(
                    f"/accounts/{account_id}/discord/dm",
                    json={"member_id": member_id, "content": content},
                )
            )
        )

    def list_discord_events(self, account_id: str) -> builtins.list[DiscordScheduledEvent]:
        return parse_list(
            DiscordScheduledEvent,
            unwrap(self._http.get(f"/accounts/{account_id}/discord/events")),
        )

    def get_discord_event(self, account_id: str, event_id: str) -> DiscordScheduledEvent:
        return DiscordScheduledEvent.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/discord/events/{event_id}"))
        )

    def create_discord_event(
        self,
        account_id: str,
        *,
        name: str,
        start_time: str,
        end_time: str | None = None,
        description: str | None = None,
        channel_id: str | None = None,
        location: str | None = None,
    ) -> DiscordScheduledEvent:
        """Name a ``channel_id`` (voice or stage), or a ``location`` with an ``end_time``."""
        body = _discord_event_body(
            name=name,
            start_time=start_time,
            end_time=end_time,
            description=description,
            channel_id=channel_id,
            location=location,
        )
        return DiscordScheduledEvent.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/discord/events", json=body))
        )

    def update_discord_event(
        self,
        account_id: str,
        event_id: str,
        *,
        name: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        description: str | None = None,
        channel_id: str | None = None,
        location: str | None = None,
        status: str | None = None,
    ) -> DiscordScheduledEvent:
        body = _discord_event_body(
            name=name,
            start_time=start_time,
            end_time=end_time,
            description=description,
            channel_id=channel_id,
            location=location,
            status=status,
        )
        return DiscordScheduledEvent.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}/discord/events/{event_id}", json=body
                )
            )
        )

    def delete_discord_event(self, account_id: str, event_id: str) -> bool:
        data = unwrap(self._http.delete(f"/accounts/{account_id}/discord/events/{event_id}"))
        return bool(data.get("deleted")) if isinstance(data, Mapping) else False

    def list_discord_members(
        self, account_id: str, *, query: str | None = None, limit: int | None = None
    ) -> builtins.list[DiscordMember]:
        """``query`` searches by username or nickname prefix."""
        params: dict[str, Any] = {}
        if query is not None:
            params["q"] = query
        if limit is not None:
            params["limit"] = limit
        return parse_list(
            DiscordMember,
            unwrap(self._http.get(f"/accounts/{account_id}/discord/members", params=params)),
        )

    def get_discord_member(self, account_id: str, member_id: str) -> DiscordMember:
        return DiscordMember.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/discord/members/{member_id}"))
        )

    def list_discord_roles(self, account_id: str) -> builtins.list[DiscordRole]:
        return parse_list(
            DiscordRole, unwrap(self._http.get(f"/accounts/{account_id}/discord/roles"))
        )

    def create_discord_role(
        self,
        account_id: str,
        *,
        name: str,
        color: int | None = None,
        hoist: bool | None = None,
        mentionable: bool | None = None,
        permissions: str | None = None,
    ) -> DiscordRole:
        body = _discord_role_body(
            name=name,
            color=color,
            hoist=hoist,
            mentionable=mentionable,
            permissions=permissions,
        )
        return DiscordRole.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/discord/roles", json=body))
        )

    def update_discord_role(
        self,
        account_id: str,
        role_id: str,
        *,
        name: str | None = None,
        color: int | None = None,
        hoist: bool | None = None,
        mentionable: bool | None = None,
        permissions: str | None = None,
    ) -> DiscordRole:
        body = _discord_role_body(
            name=name,
            color=color,
            hoist=hoist,
            mentionable=mentionable,
            permissions=permissions,
        )
        return DiscordRole.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}/discord/roles/{role_id}", json=body
                )
            )
        )

    def delete_discord_role(self, account_id: str, role_id: str) -> bool:
        data = unwrap(self._http.delete(f"/accounts/{account_id}/discord/roles/{role_id}"))
        return bool(data.get("deleted")) if isinstance(data, Mapping) else False

    def add_discord_member_role(self, account_id: str, role_id: str, member_id: str) -> bool:
        data = unwrap(
            self._http.request(
                "PUT", f"/accounts/{account_id}/discord/roles/{role_id}/members/{member_id}"
            )
        )
        return bool(data.get("assigned")) if isinstance(data, Mapping) else False

    def remove_discord_member_role(self, account_id: str, role_id: str, member_id: str) -> bool:
        data = unwrap(
            self._http.delete(f"/accounts/{account_id}/discord/roles/{role_id}/members/{member_id}")
        )
        return bool(data.get("assigned")) if isinstance(data, Mapping) else False


def _discord_event_body(**fields: Any) -> dict[str, Any]:
    """Only the fields the caller named; Discord keeps the rest as they are."""
    return {k: v for k, v in fields.items() if v is not None}


def _discord_role_body(**fields: Any) -> dict[str, Any]:
    return {k: v for k, v in fields.items() if v is not None}
