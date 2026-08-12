"""Response models.

Fields are snake_case in Python. The API is not consistent about its wire
casing — posts come back snake_case, accounts camelCase, workspaces a mix — so
every field accepts both spellings via ``AliasChoices``. Unknown keys are kept
rather than dropped, so a server-side addition never breaks a client.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import AliasChoices, AliasGenerator, BaseModel, ConfigDict

__all__ = [
    "PLATFORMS",
    "POST_STATUSES",
    "Platform",
    "PostStatus",
    "AiCreditBalance",
    "AiCredits",
    "CaptionResult",
    "ContentBlock",
    "Delivery",
    "Label",
    "MediaItem",
    "OwlstackModel",
    "Page",
    "PageMeta",
    "Post",
    "PostAccount",
    "RepurposeResult",
    "RewriteResult",
    "RewriteVariant",
    "SocialAccount",
    "Workspace",
]

#: Every platform the API can publish to. Model fields stay plain `str`, so a
#: platform added server-side still parses on an older SDK.
PLATFORMS: tuple[str, ...] = (
    "twitter",
    "linkedin",
    "facebook",
    "instagram",
    "instagram-business",
    "telegram",
    "twitch",
    "discord",
    "slack",
    "reddit",
    "pinterest",
    "tumblr",
    "dribbble",
    "mewe",
    "tiktok",
    "youtube",
    "bluesky",
    "threads",
    "mastodon",
    "lemmy",
    "devto",
    "hashnode",
    "medium",
    "substack",
    "google-business",
    "kick",
    "listmonk",
    "wordpress",
    "nostr",
    "whop",
    "skool",
)

Platform = Literal[
    "twitter",
    "linkedin",
    "facebook",
    "instagram",
    "instagram-business",
    "telegram",
    "twitch",
    "discord",
    "slack",
    "reddit",
    "pinterest",
    "tumblr",
    "dribbble",
    "mewe",
    "tiktok",
    "youtube",
    "bluesky",
    "threads",
    "mastodon",
    "lemmy",
    "devto",
    "hashnode",
    "medium",
    "substack",
    "google-business",
    "kick",
    "listmonk",
    "wordpress",
    "nostr",
    "whop",
    "skool",
]

PostStatus = Literal[
    "draft",
    "pending_approval",
    "scheduled",
    "publishing",
    "published",
    "failed",
    "cancelled",
]

POST_STATUSES: tuple[str, ...] = (
    "draft",
    "pending_approval",
    "scheduled",
    "publishing",
    "published",
    "failed",
    "cancelled",
)


def _to_camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


def _aliases(name: str) -> AliasChoices:
    camel = _to_camel(name)
    return AliasChoices(name, camel) if camel != name else AliasChoices(name)


class OwlstackModel(BaseModel):
    """Base for every response model."""

    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=_aliases),
        populate_by_name=True,
        extra="allow",
    )


class MediaItem(OwlstackModel):
    type: Literal["image", "video", "gif"] | str
    name: str | None = None
    url: str
    size: int | None = None
    alt: str | None = None
    thumbnail: str | None = None


class ContentBlock(OwlstackModel):
    id: int | str | None = None
    text: str | None = None
    media: list[MediaItem] = []
    position: int | None = None


class PostAccount(OwlstackModel):
    """An account a post is targeted at, plus its per-account delivery state."""

    id: str
    platform: str
    username: str | None = None
    name: str | None = None
    avatar: str | None = None
    publish_status: str | None = None
    posted_at: datetime | None = None
    platform_post_id: str | None = None
    external_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    attempts: int | None = None
    max_attempts: int | None = None


class Label(OwlstackModel):
    id: str
    name: str
    color: str | None = None
    workspace: dict[str, Any] | None = None


class Post(OwlstackModel):
    id: str
    workspace_id: str | None = None
    status: str
    content_type: str | None = None
    schedule_at: datetime | None = None
    title: str | None = None
    summary: str | None = None
    repeatable: bool | None = None
    repeatable_times: int | None = None
    repeatable_gap: int | None = None
    repeatable_gap_unit: str | None = None
    remaining_posts: int | None = None
    auto_plug: bool | None = None
    auto_plug_content: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    content: list[ContentBlock] = []
    accounts: list[PostAccount] = []
    labels: list[Label] = []
    settings: dict[str, dict[str, Any]] = {}
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SocialAccount(OwlstackModel):
    """A connected social account. Named to avoid shadowing user accounts."""

    id: str
    workspace_id: str | None = None
    platform: str
    username: str | None = None
    name: str | None = None
    avatar: str | None = None
    active: bool | None = None
    is_primary: bool | None = None
    health_status: str | None = None
    last_health_check: datetime | None = None


class Workspace(OwlstackModel):
    id: str
    name: str
    slug: str | None = None
    type: str | None = None
    logo: str | None = None
    website: str | None = None
    timezone: str | None = None
    country: str | None = None
    description: str | None = None
    language: str | None = None
    require_approval: bool | None = None
    ai_alt_text_enabled: bool | None = None
    brand_color: str | None = None
    role: str | None = None
    created_at: datetime | None = None
    accounts: list[SocialAccount] = []


class Delivery(OwlstackModel):
    """One post-to-account delivery attempt."""

    id: str
    account_id: str | None = None
    status: str | None = None
    platform: str | None = None
    username: str | None = None
    account_name: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    attempts: int | None = None
    max_attempts: int | None = None
    scheduled_publish_at: datetime | None = None
    delay_reason: str | None = None
    delay_message: str | None = None
    posted_at: datetime | None = None
    last_attempt_at: datetime | None = None
    platform_post_id: str | None = None
    external_url: str | None = None


class PageMeta(OwlstackModel):
    current_page: int | None = None
    per_page: int | None = None
    total: int | None = None
    last_page: int | None = None
    from_: int | None = None
    to: int | None = None

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda name: (
                AliasChoices("from", "from_") if name == "from_" else _aliases(name)
            )
        ),
        populate_by_name=True,
        extra="allow",
    )


T = TypeVar("T", bound=OwlstackModel)


class Page(OwlstackModel, Generic[T]):
    """One page of a list endpoint: its items plus the pagination meta."""

    items: list[T] = []
    meta: PageMeta = PageMeta()

    def __iter__(self) -> Any:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> T:
        return self.items[index]


class AiCredits(OwlstackModel):
    """Credits charged by one AI call, and what is left afterwards."""

    charged: int
    remaining: int


class AiCreditBalance(OwlstackModel):
    credits_remaining: int
    credits_used: int
    credits_total: int
    period_start: datetime | None = None
    period_end: datetime | None = None


class CaptionResult(OwlstackModel):
    caption: str
    credits: AiCredits | None = None


class RewriteVariant(OwlstackModel):
    platform: str
    content: str
    credits: int | None = None


class RewriteResult(OwlstackModel):
    results: list[RewriteVariant] = []
    credits: AiCredits | None = None


class RepurposeResult(OwlstackModel):
    url: str
    title: str | None = None
    posts: dict[str, str] = {}
    credits: AiCredits | None = None
