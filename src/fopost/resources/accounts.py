"""``client.accounts`` — the social accounts connected to a workspace."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote

from .._http import unwrap
from ..models import (
    AccountMove,
    AccountRename,
    RedditDefaultSubreddit,
    RedditFlairs,
    RedditSubreddit,
    RedditSubredditRules,
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

    def list_reddit_subreddits(self, account_id: str) -> builtins.list[RedditSubreddit]:
        """Subreddits the account is in, busiest first, plus its own profile page."""
        return parse_list(
            RedditSubreddit, unwrap(self._http.get(f"/accounts/{account_id}/reddit/subreddits"))
        )

    def list_reddit_subreddit_rules(self, account_id: str, subreddit: str) -> RedditSubredditRules:
        """The rules a subreddit publishes, in its own order."""
        return RedditSubredditRules.model_validate(
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/reddit/subreddits/{quote(subreddit, safe='')}/rules"
                )
            )
        )

    def list_reddit_flairs(self, account_id: str, subreddit: str) -> RedditFlairs:
        """Post flairs one subreddit offers; a flair id is valid only there."""
        return RedditFlairs.model_validate(
            unwrap(
                self._http.get(f"/accounts/{account_id}/reddit/flairs", {"subreddit": subreddit})
            )
        )

    def set_reddit_default_subreddit(
        self, account_id: str, subreddit: str | None
    ) -> RedditDefaultSubreddit:
        """Where posts go when a post names none; ``None`` falls back to the profile page."""
        return RedditDefaultSubreddit.model_validate(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/reddit/default-subreddit", {"subreddit": subreddit}
                )
            )
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
