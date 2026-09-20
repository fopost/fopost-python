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
    "AccountGroup",
    "AccountMove",
    "ACTIVITY_KINDS",
    "ActivityKind",
    "ActivityActor",
    "ActivityEvent",
    "ActivityPage",
    "AccountRename",
    "Ad",
    "AdConnection",
    "AdInsights",
    "AdSource",
    "AiCreditBalance",
    "AiCredits",
    "Audience",
    "AudiencesResult",
    "BoostablePost",
    "CaptionResult",
    "ContentBlock",
    "Delivery",
    "ExternalAd",
    "InboxAccount",
    "InboxAccountRef",
    "InboxApproval",
    "InboxAttachment",
    "InboxConversation",
    "InboxItem",
    "InboxPlatform",
    "InboxPostContext",
    "InboxRefreshResult",
    "InboxReplyResult",
    "InboxStartConversationResult",
    "InboxThread",
    "Label",
    "Lead",
    "LeadForm",
    "LeadFormSource",
    "LeadsPage",
    "MediaItem",
    "FopostModel",
    "Page",
    "PageMeta",
    "Post",
    "PostAccount",
    "PresignedUpload",
    "RepurposeResult",
    "RewriteResult",
    "RewriteVariant",
    "SlackChannel",
    "SlackIdentity",
    "SlackMember",
    "SocialAccount",
    "TargetingOption",
    "TelegramBotCommand",
    "TelegramBotCommands",
    "TelegramConnectCode",
    "TelegramConnectStatus",
    "ValidateLengthCheck",
    "ValidateLengthResult",
    "ValidateMediaResult",
    "ValidatePlatformCheck",
    "ValidatePostResult",
    "ContentSignal",
    "Workspace",
    "AdAccountTree",
    "AdCampaign",
    "AdCampaignNode",
    "AdCreative",
    "AdInsightsReport",
    "AdSet",
    "AdSetNode",
    "BulkAdStatusResult",
    "FeedLead",
    "InsightsMetrics",
    "InsightsRow",
    "LeadFormDetail",
    "LeadPage",
    "LeadPageSubscription",
    "LeadsFeedPage",
    "NetworkAd",
    "ReachEstimate",
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


class FopostModel(BaseModel):
    """Base for every response model."""

    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=_aliases),
        populate_by_name=True,
        extra="allow",
    )


class MediaItem(FopostModel):
    id: str | None = None
    type: Literal["image", "video", "gif", "document"] | str
    name: str | None = None
    url: str
    preview_url: str | None = None
    size: int | None = None
    alt: str | None = None
    thumbnail: str | None = None


class PresignedUpload(FopostModel):
    """A one-time upload slot: PUT the bytes to ``upload_url`` with ``headers``."""

    upload_id: str
    upload_url: str
    method: str = "PUT"
    headers: dict[str, str] = {}
    expires_at: datetime | None = None


class ContentBlock(FopostModel):
    id: int | str | None = None
    text: str | None = None
    media: list[MediaItem] = []
    position: int | None = None


class PostAccount(FopostModel):
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


class Label(FopostModel):
    id: str
    name: str
    color: str | None = None
    workspace: dict[str, Any] | None = None


class Post(FopostModel):
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


class SocialAccount(FopostModel):
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
    platform_name: str | None = None


class AccountRename(FopostModel):
    """``name`` is the display override when set, else the platform name."""

    id: str
    name: str | None = None
    platform_name: str | None = None


class AccountMove(FopostModel):
    id: str
    workspace_id: str


class AccountGroup(FopostModel):
    """A named set of connected accounts in one workspace."""

    id: str
    name: str
    account_ids: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TelegramConnectCode(FopostModel):
    """A one-time code; send ``command`` (``/connect <code>``) to the bot in a chat."""

    code: str
    command: str
    bot_username: str | None = None
    deep_link: str | None = None
    group_link: str | None = None
    expires_at: datetime | None = None


class TelegramConnectStatus(FopostModel):
    """``status`` is ``pending``, ``connected``, ``failed`` or ``expired``."""

    status: str
    account_id: str | None = None
    reason: str | None = None


class TelegramBotCommand(FopostModel):
    command: str
    description: str


class TelegramBotCommands(FopostModel):
    commands: list[TelegramBotCommand] = []


class SlackChannel(FopostModel):
    """``is_current`` marks the channel this account posts to."""

    id: str
    name: str
    is_private: bool = False
    is_member: bool = False
    is_current: bool = False


class SlackMember(FopostModel):
    """``id`` is the handle for starting a DM through ``inbox.start_conversation``."""

    id: str
    name: str
    real_name: str | None = None
    display_name: str | None = None
    avatar: str | None = None
    is_bot: bool = False


class SlackIdentity(FopostModel):
    """The name and icon posts appear under; ``None`` means the app default."""

    username: str | None = None
    icon_url: str | None = None
    icon_emoji: str | None = None


class Workspace(FopostModel):
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


class Delivery(FopostModel):
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


class PageMeta(FopostModel):
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


T = TypeVar("T", bound=FopostModel)


class Page(FopostModel, Generic[T]):
    """One page of a list endpoint: its items plus the pagination meta."""

    items: list[T] = []
    meta: PageMeta = PageMeta()

    def __iter__(self) -> Any:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> T:
        return self.items[index]


class AiCredits(FopostModel):
    """Credits charged by one AI call, and what is left afterwards."""

    charged: int
    remaining: int


class AiCreditBalance(FopostModel):
    credits_remaining: int
    credits_used: int
    credits_total: int
    period_start: datetime | None = None
    period_end: datetime | None = None


class CaptionResult(FopostModel):
    caption: str
    credits: AiCredits | None = None


class RewriteVariant(FopostModel):
    platform: str
    content: str
    credits: int | None = None


class RewriteResult(FopostModel):
    results: list[RewriteVariant] = []
    credits: AiCredits | None = None


class RepurposeResult(FopostModel):
    url: str
    title: str | None = None
    posts: dict[str, str] = {}
    credits: AiCredits | None = None


# ─── Inbox ───────────────────────────────────────────────────────────


class InboxAccountRef(FopostModel):
    id: str
    platform: str
    username: str | None = None
    name: str | None = None
    avatar: str | None = None


class InboxAttachment(FopostModel):
    kind: str
    name: str | None = None
    width: int | None = None
    height: int | None = None
    link: str | None = None
    #: Served by the API, never a platform URL.
    url: str | None = None
    preview_url: str | None = None


class InboxPostContext(FopostModel):
    """The platform post an item sits under, whoever published it."""

    external_id: str | None = None
    is_own: bool | None = None
    text: str | None = None
    author_name: str | None = None
    author_handle: str | None = None
    author_avatar_url: str | None = None
    thumbnail_url: str | None = None
    permalink: str | None = None
    published_at: datetime | None = None
    #: The FoPost post this was published from, when it was.
    published: dict[str, Any] | None = None


class InboxItem(FopostModel):
    """A comment, mention or direct message on a connected account."""

    id: str
    workspace_id: str | None = None
    platform: str
    type: str
    state: str
    direction: str | None = None
    conversation_id: str | None = None
    author_name: str | None = None
    author_handle: str | None = None
    author_avatar_url: str | None = None
    text: str | None = None
    attachments: list[InboxAttachment] = []
    permalink: str | None = None
    post_external_id: str | None = None
    parent_external_id: str | None = None
    platform_created_at: datetime | None = None
    snoozed_until: datetime | None = None
    replied_at: datetime | None = None
    created_at: datetime | None = None
    can_reply: bool | None = None
    hidden: bool | None = None
    can_hide: bool | None = None
    can_delete: bool | None = None
    liked: bool | None = None
    pinned: bool | None = None
    reaction: str | None = None
    edited_at: datetime | None = None
    can_like: bool | None = None
    can_pin: bool | None = None
    can_edit: bool | None = None
    can_react: bool | None = None
    can_send_media: bool | None = None
    can_quick_reply: bool | None = None
    can_private_reply: bool | None = None
    post: dict[str, Any] | None = None
    post_context: InboxPostContext | None = None
    account: InboxAccountRef | None = None


class InboxThread(FopostModel):
    """One platform post and the comments it has collected."""

    workspace_id: str | None = None
    account_id: str
    post_external_id: str | None = None
    comment_count: int = 0
    unread_count: int = 0
    last_comment_at: datetime | None = None
    last_comment_text: str | None = None
    last_comment_author: str | None = None
    post: InboxPostContext | None = None
    account: InboxAccountRef | None = None


class InboxConversation(FopostModel):
    """One direct-message thread."""

    workspace_id: str | None = None
    account_id: str
    conversation_id: str
    message_count: int = 0
    unread_count: int = 0
    last_message_at: datetime | None = None
    last_message_text: str | None = None
    last_message_outbound: bool | None = None
    participant: dict[str, Any] | None = None
    account: InboxAccountRef | None = None


class InboxAccount(FopostModel):
    id: str
    workspace_id: str | None = None
    platform: str
    username: str | None = None
    name: str | None = None
    avatar: str | None = None
    inbox_supported: bool | None = None
    pending_reason: str | None = None
    dm_supported: bool | None = None
    dm_pending_reason: str | None = None
    can_start_conversation: bool | None = None


class InboxPlatform(FopostModel):
    platform: str
    comments: str
    dms: str


class InboxApproval(FopostModel):
    """A drafted reply a person still has to send."""

    id: int
    workspace_id: str | None = None
    source: str | None = None
    reply: str
    created_at: datetime | None = None
    item: dict[str, Any] | None = None


class InboxReplyResult(FopostModel):
    item: InboxItem
    reply: dict[str, Any] = {}


class InboxStartConversationResult(FopostModel):
    conversation_id: str | None = None
    item: InboxItem | None = None


class InboxRefreshResult(FopostModel):
    accounts_polled: int = 0
    new_items: int = 0
    rate_limited: int = 0
    dm_reconnect: list[dict[str, Any]] = []


# ─── Ads ─────────────────────────────────────────────────────────────


class AdInsights(FopostModel):
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    #: Ad account currency, minor units.
    spend_minor: int = 0


class Ad(FopostModel):
    """A boost or standalone ad created through FoPost."""

    id: str
    workspace_id: str | None = None
    kind: str
    name: str
    goal: str
    status: str
    effective_status: str | None = None
    connection_id: str | None = None
    account_id: str | None = None
    platform: str | None = None
    ad_account_id: str | None = None
    source_post_id: str | None = None
    budget_minor: int | None = None
    budget_type: str | None = None
    currency: str | None = None
    end_at: datetime | None = None
    targeting: dict[str, Any] = {}
    creative: dict[str, Any] | None = None
    insights: AdInsights | None = None
    insights_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime | None = None


class ExternalAd(FopostModel):
    """An ad on a connected ad account that was made outside FoPost."""

    id: str
    name: str
    effective_status: str | None = None
    campaign_id: str | None = None
    campaign_name: str | None = None
    objective: str | None = None
    budget_minor: int | None = None
    budget_type: str | None = None
    end_at: datetime | None = None
    created_at: datetime | None = None
    connection_id: str | None = None
    ad_account_id: str | None = None
    currency: str | None = None
    workspace_id: str | None = None


class AdConnection(FopostModel):
    id: str
    provider: str | None = None
    auth_type: str | None = None
    name: str
    business_id: str | None = None
    created_at: datetime | None = None
    workspace_id: str | None = None


class AdSource(FopostModel):
    """A connection with the ad accounts and Pages its grant reaches."""

    connection_id: str
    name: str
    workspace_id: str | None = None
    ad_accounts: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    error: str | None = None


class BoostablePost(FopostModel):
    id: str
    workspace_id: str | None = None
    text: str | None = None
    thumbnail_url: str | None = None
    deliveries: list[dict[str, Any]] = []


class Audience(FopostModel):
    id: str
    name: str
    subtype: str | None = None
    description: str | None = None
    size_lower: int | None = None
    size_upper: int | None = None
    delivery_status: str | None = None
    created_at: str | None = None


class AudiencesResult(FopostModel):
    audiences: list[Audience] = []
    pixels: list[dict[str, Any]] = []
    workspace_id: str | None = None


class TargetingOption(FopostModel):
    id: str
    name: str
    detail: str | None = None


class LeadForm(FopostModel):
    id: str
    name: str
    status: str | None = None
    leads_count: int = 0
    created_at: str | None = None
    questions: list[str] = []


class LeadFormSource(FopostModel):
    connection_id: str
    connection_name: str | None = None
    page_id: str | None = None
    page_name: str | None = None
    forms: list[LeadForm] = []
    error: str | None = None
    workspace_id: str | None = None


class Lead(FopostModel):
    id: str
    created_at: str | None = None
    fields: list[dict[str, Any]] = []
    ad_name: str | None = None
    campaign_name: str | None = None
    platform: str | None = None
    is_organic: bool | None = None


class LeadsPage(FopostModel):
    leads: list[Lead] = []
    next_cursor: str | None = None


class AdCampaign(FopostModel):
    """A campaign on Meta, read live."""

    id: str
    name: str
    status: str
    effective_status: str | None = None
    objective: str | None = None
    #: None when the budget lives on the ad sets.
    budget_minor: int | None = None
    budget_type: str | None = None
    created_at: str | None = None


class AdSet(FopostModel):
    """An ad set on Meta, read live."""

    id: str
    name: str
    campaign_id: str | None = None
    status: str
    effective_status: str | None = None
    budget_minor: int | None = None
    budget_type: str | None = None
    end_at: str | None = None
    optimization_goal: str | None = None
    created_at: str | None = None


class NetworkAd(FopostModel):
    """An ad inside an ad set on Meta, read live. Not the same as a FoPost ``Ad``."""

    id: str
    name: str
    campaign_id: str | None = None
    ad_set_id: str | None = None
    creative_id: str | None = None
    status: str
    effective_status: str | None = None
    created_at: str | None = None


class AdSetNode(AdSet):
    ads: list[NetworkAd] = []


class AdCampaignNode(AdCampaign):
    ad_sets: list[AdSetNode] = []


class AdAccountTree(FopostModel):
    """Campaigns, their ad sets and their ads on one ad account."""

    ad_account_id: str
    currency: str | None = None
    workspace_id: str | None = None
    campaigns: list[AdCampaignNode] = []


class BulkAdStatusResult(FopostModel):
    id: str
    level: str
    ok: bool
    error: str | None = None


class AdCreative(FopostModel):
    id: str
    name: str
    format: str
    status: str | None = None
    title: str | None = None
    body: str | None = None
    link: str | None = None
    thumbnail_url: str | None = None
    call_to_action: str | None = None
    url_tags: str | None = None


class InsightsMetrics(FopostModel):
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    #: Account currency, minor units.
    spend_minor: int = 0
    #: Clicks per impression, as a percentage.
    ctr: float = 0
    leads: int = 0


class InsightsRow(FopostModel):
    """A breakdown row carries ``key``; a timeline row carries ``date``."""

    key: str | None = None
    date: str | None = None
    metrics: InsightsMetrics


class AdInsightsReport(FopostModel):
    object_id: str
    currency: str | None = None
    since: str
    until: str
    breakdown_by: str | None = None
    totals: InsightsMetrics | None = None
    breakdown: list[InsightsRow] = []
    timeline: list[InsightsRow] = []


class ReachEstimate(FopostModel):
    lower: int | None = None
    upper: int | None = None
    ready: bool = False


class LeadFormDetail(LeadForm):
    page_id: str | None = None
    privacy_policy_url: str | None = None
    locale: str | None = None


class FeedLead(FopostModel):
    """A lead stored by FoPost from a subscribed Page."""

    id: str
    lead_id: str
    connection_id: str | None = None
    page_id: str | None = None
    form_id: str | None = None
    ad_id: str | None = None
    ad_name: str | None = None
    campaign_name: str | None = None
    platform: str | None = None
    is_organic: bool = False
    fields: list[dict[str, Any]] = []
    submitted_at: datetime | None = None
    workspace_id: str | None = None


class LeadsFeedPage(FopostModel):
    leads: list[FeedLead] = []
    next_cursor: str | None = None


class LeadPage(FopostModel):
    """A Page whose leads FoPost stores."""

    connection_id: str
    page_id: str
    page_name: str | None = None
    created_at: datetime | None = None
    workspace_id: str | None = None


class LeadPageSubscription(FopostModel):
    page_id: str
    #: Leads already on the Page, stored on subscribe.
    backfilled: int = 0


class ContentSignal(FopostModel):
    level: Literal["info", "warn"] | str
    code: str
    message: str


class ValidatePlatformCheck(FopostModel):
    platform: str
    ready: bool
    issues: list[str] = []
    score: float | None = None
    signals: list[ContentSignal] = []


class ValidatePostResult(FopostModel):
    ready: bool
    platforms: list[ValidatePlatformCheck] = []


class ValidateLengthCheck(FopostModel):
    platform: str
    length: int
    limit: int | None = None
    unit: Literal["chars", "bytes"] | str
    ok: bool
    signals: list[ContentSignal] = []


class ValidateLengthResult(FopostModel):
    ok: bool
    platforms: list[ValidateLengthCheck] = []


class ValidateMediaResult(FopostModel):
    ok: bool
    issues: list[str] = []
    name: str | None = None
    size: int | None = None
    mime_type: str | None = None
    type: str | None = None


ACTIVITY_KINDS = (
    "publish",
    "connection",
    "webhook",
    "inbox",
    "automation",
    "billing",
    "security",
)
ActivityKind = Literal[
    "publish", "connection", "webhook", "inbox", "automation", "billing", "security"
]


class ActivityActor(FopostModel):
    """Who did it. ``name`` is absent for a system event."""

    type: Literal["user", "api_key", "agent", "system"]
    name: str | None = None


class ActivityEvent(FopostModel):
    id: str
    workspace_id: str | None = None
    kind: str
    ref_type: str | None = None
    ref_id: str | None = None
    summary: str
    actor: ActivityActor
    time: datetime


class ActivityPage(FopostModel):
    """One page of activity, newest first, plus the cursor for the next."""

    items: list[ActivityEvent] = []
    next_cursor: str | None = None

    def __iter__(self) -> Any:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> ActivityEvent:
        return self.items[index]
