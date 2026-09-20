"""``client.accounts`` — the social accounts connected to a workspace."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    AccountMove,
    AccountRename,
    BlueskyLanguages,
    DiscordChannel,
    DiscordIdentity,
    DiscordMember,
    DiscordMessage,
    DiscordMessageRef,
    DiscordRole,
    DiscordScheduledEvent,
    InstagramAudio,
    InstagramPublishingLimit,
    InstagramStory,
    InstagramStoryInsights,
    LinkedInMention,
    MetaGreeting,
    MetaGreetingText,
    MetaIceBreaker,
    MetaIceBreakers,
    MetaPersistentMenu,
    MetaPersistentMenuEntry,
    PinterestBoard,
    SlackChannel,
    SlackIdentity,
    SlackMember,
    SocialAccount,
    TelegramBotCommand,
    TelegramBotCommands,
    TelegramConnectCode,
    TelegramConnectStatus,
    TikTokCreatorInfo,
    TikTokMusic,
    TikTokPlace,
    TikTokVideoSource,
    WebhookSubscription,
    YouTubeCaptionTrack,
    YouTubePlaylist,
    YouTubeTranscript,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["AccountsResource"]


def _dump(value: Any) -> dict[str, Any]:
    """A model or a plain mapping, as the body the API takes."""
    if hasattr(value, "model_dump"):
        dumped: dict[str, Any] = value.model_dump(exclude_none=True)
        return dumped
    return {k: v for k, v in dict(value).items() if v is not None}


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

    # ── Meta messaging settings (Facebook Pages, Instagram) ──────────

    def get_ice_breakers(self, account_id: str) -> MetaIceBreakers:
        """The prompts shown before the first message; networks without them answer 400."""
        return MetaIceBreakers.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/messaging/ice-breakers"))
        )

    def set_ice_breakers(
        self,
        account_id: str,
        ice_breakers: Sequence[MetaIceBreaker | Mapping[str, str]],
    ) -> MetaIceBreakers:
        """Replace the ice breakers. Up to four."""
        payload = [_dump(item) for item in ice_breakers]
        return MetaIceBreakers.model_validate(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/messaging/ice-breakers", {"ice_breakers": payload}
                )
            )
        )

    def delete_ice_breakers(self, account_id: str) -> MetaIceBreakers:
        return MetaIceBreakers.model_validate(
            unwrap(self._http.delete(f"/accounts/{account_id}/messaging/ice-breakers"))
        )

    def get_persistent_menu(self, account_id: str) -> MetaPersistentMenu:
        """The always-visible Messenger menu. Facebook Pages only."""
        return MetaPersistentMenu.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/messaging/persistent-menu"))
        )

    def set_persistent_menu(
        self,
        account_id: str,
        menu: Sequence[MetaPersistentMenuEntry | Mapping[str, Any]],
    ) -> MetaPersistentMenu:
        """Replace the menu, one entry per locale, up to three items each."""
        payload = [_dump(entry) for entry in menu]
        return MetaPersistentMenu.model_validate(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/messaging/persistent-menu",
                    {"persistent_menu": payload},
                )
            )
        )

    def delete_persistent_menu(self, account_id: str) -> MetaPersistentMenu:
        return MetaPersistentMenu.model_validate(
            unwrap(self._http.delete(f"/accounts/{account_id}/messaging/persistent-menu"))
        )

    def get_greeting(self, account_id: str) -> MetaGreeting:
        """The text shown before a Messenger conversation starts. Facebook Pages only."""
        return MetaGreeting.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/messaging/greeting"))
        )

    def set_greeting(
        self,
        account_id: str,
        greeting: Sequence[MetaGreetingText | Mapping[str, str]],
    ) -> MetaGreeting:
        """Replace the greeting, one entry per locale, each up to 160 characters."""
        payload = [_dump(item) for item in greeting]
        return MetaGreeting.model_validate(
            unwrap(
                self._http.put(f"/accounts/{account_id}/messaging/greeting", {"greeting": payload})
            )
        )

    def delete_greeting(self, account_id: str) -> MetaGreeting:
        return MetaGreeting.model_validate(
            unwrap(self._http.delete(f"/accounts/{account_id}/messaging/greeting"))
        )

    def get_webhook_subscription(self, account_id: str) -> WebhookSubscription:
        """What the network is delivering to the FoPost webhook for this account."""
        return WebhookSubscription.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/webhook-subscription"))
        )

    def resubscribe_webhook(self, account_id: str) -> WebhookSubscription:
        """Subscribe to every field this account needs, lapsed or not."""
        return WebhookSubscription.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/webhook-subscription"))
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

    # ─── Per-network extras ──────────────────────────────────────

    def list_pinterest_boards(self, account_id: str) -> builtins.list[PinterestBoard]:
        """Boards this Pinterest connection can pin to."""
        return parse_list(
            PinterestBoard, unwrap(self._http.get(f"/accounts/{account_id}/pinterest/boards"))
        )

    def create_pinterest_board(
        self,
        account_id: str,
        *,
        name: str,
        description: str | None = None,
        privacy: str | None = None,
    ) -> PinterestBoard:
        """``privacy`` is ``PUBLIC``, ``PROTECTED`` or ``SECRET``."""
        body = drop_unset(
            {
                "name": name,
                "description": description if description is not None else UNSET,
                "privacy": privacy if privacy is not None else UNSET,
            }
        )
        return PinterestBoard.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/pinterest/boards", body))
        )

    def list_youtube_playlists(self, account_id: str) -> builtins.list[YouTubePlaylist]:
        """The channel's own playlists, with the stored default marked."""
        return parse_list(
            YouTubePlaylist, unwrap(self._http.get(f"/accounts/{account_id}/youtube/playlists"))
        )

    def create_youtube_playlist(
        self,
        account_id: str,
        *,
        title: str,
        description: str | None = None,
        privacy: str | None = None,
    ) -> YouTubePlaylist:
        body = drop_unset(
            {
                "title": title,
                "description": description if description is not None else UNSET,
                "privacy": privacy if privacy is not None else UNSET,
            }
        )
        return YouTubePlaylist.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/youtube/playlists", body))
        )

    def set_default_youtube_playlist(self, account_id: str, playlist_id: str | None) -> str | None:
        """The playlist a new video joins when the post picks none; ``None`` clears it."""
        data = unwrap(
            self._http.put(
                f"/accounts/{account_id}/youtube/playlists/default",
                {"playlist_id": playlist_id},
            )
        )
        stored = data.get("playlist_id")
        return stored if isinstance(stored, str) else None

    def list_youtube_captions(
        self, account_id: str, video_id: str
    ) -> builtins.list[YouTubeCaptionTrack]:
        return parse_list(
            YouTubeCaptionTrack,
            unwrap(self._http.get(f"/accounts/{account_id}/youtube/videos/{video_id}/captions")),
        )

    def upload_youtube_captions(
        self,
        account_id: str,
        video_id: str,
        *,
        language: str,
        body: str,
        name: str | None = None,
        is_draft: bool | None = None,
    ) -> YouTubeCaptionTrack:
        """``body`` is the subtitle file; YouTube reads SRT and WebVTT and sniffs which."""
        payload = drop_unset(
            {
                "language": language,
                "body": body,
                "name": name if name is not None else UNSET,
                "is_draft": is_draft if is_draft is not None else UNSET,
            }
        )
        return YouTubeCaptionTrack.model_validate(
            unwrap(
                self._http.post(
                    f"/accounts/{account_id}/youtube/videos/{video_id}/captions", payload
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

    def read_youtube_transcript(self, account_id: str, caption_id: str) -> YouTubeTranscript:
        return YouTubeTranscript.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/youtube/captions/{caption_id}"))
        )

    def get_bluesky_languages(self, account_id: str) -> BlueskyLanguages:
        """What a post from this connection is written in when it does not say."""
        return BlueskyLanguages.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/bluesky/languages"))
        )

    def set_bluesky_languages(self, account_id: str, languages: Sequence[str]) -> BlueskyLanguages:
        """Up to three BCP-47 tags; an empty list clears the default."""
        return BlueskyLanguages.model_validate(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/bluesky/languages", {"languages": list(languages)}
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

    def get_tiktok_creator_info(self, account_id: str) -> TikTokCreatorInfo:
        """The switches TikTok enforces at publish time, changed in the TikTok app."""
        return TikTokCreatorInfo.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/tiktok/creator-info"))
        )

    def search_tiktok_music(
        self, account_id: str, *, q: str, limit: int | None = None
    ) -> builtins.list[TikTokMusic]:
        """TikTok's Commercial Music Library.

        Needs the Marketing API product on the TikTok app; without it the call
        raises rather than answering an empty list.
        """
        return parse_list(
            TikTokMusic,
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/tiktok/music", params={"q": q, "limit": limit}
                )
            ),
        )

    def search_tiktok_locations(
        self, account_id: str, *, q: str, limit: int | None = None
    ) -> builtins.list[TikTokPlace]:
        """Places a post can be tagged with. Same TikTok product as the music library."""
        return parse_list(
            TikTokPlace,
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/tiktok/locations", params={"q": q, "limit": limit}
                )
            ),
        )

    def lookup_tiktok_video(self, account_id: str, url: str) -> TikTokVideoSource:
        """Resolve a share link to one of this account's own videos, for repurposing."""
        return TikTokVideoSource.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/tiktok/video-download", {"url": url}))
        )

    def search_instagram_audio(
        self, account_id: str, *, q: str | None = None, audio_type: str | None = None
    ) -> builtins.list[InstagramAudio]:
        """Tracks a Reel can carry; with no query Instagram answers with what is trending."""
        params = {"q": q, "audio_type": audio_type}
        return parse_list(
            InstagramAudio,
            unwrap(self._http.get(f"/accounts/{account_id}/instagram/audio", params=params)),
        )

    def get_instagram_publishing_limit(self, account_id: str) -> InstagramPublishingLimit:
        """How many posts are left before Instagram refuses the next one."""
        return InstagramPublishingLimit.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/instagram/publishing-limit"))
        )

    def list_instagram_stories(
        self, account_id: str, *, insights: bool | None = None
    ) -> builtins.list[InstagramStory]:
        """Stories still inside their 24 hours, posted through FoPost or not."""
        return parse_list(
            InstagramStory,
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/instagram/stories", params={"insights": insights}
                )
            ),
        )

    def get_instagram_story_insights(
        self, account_id: str, story_id: str
    ) -> InstagramStoryInsights:
        return InstagramStoryInsights.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/instagram/stories/{story_id}/insights"))
        )

    def search_linkedin_mentions(self, account_id: str, q: str) -> builtins.list[LinkedInMention]:
        """Organizations a post can mention. People are not searchable on LinkedIn."""
        return parse_list(
            LinkedInMention,
            unwrap(self._http.get(f"/accounts/{account_id}/linkedin/mentions", params={"q": q})),
        )


def _discord_event_body(**fields: Any) -> dict[str, Any]:
    """Only the fields the caller named; Discord keeps the rest as they are."""
    return {k: v for k, v in fields.items() if v is not None}


def _discord_role_body(**fields: Any) -> dict[str, Any]:
    return {k: v for k, v in fields.items() if v is not None}
