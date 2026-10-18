# fopost

[![PyPI](https://img.shields.io/pypi/v/fopost.svg)](https://pypi.org/project/fopost/)
[![Python versions](https://img.shields.io/pypi/pyversions/fopost.svg)](https://pypi.org/project/fopost/)
[![CI](https://github.com/fopost/fopost-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fopost/fopost-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Official Python SDK for the [FoPost](https://fopost.com) API. Schedule and publish to +30 social platforms from your code.

```bash
pip install fopost
```

Requires Python 3.10 or newer. Built on `httpx` and `pydantic` v2, fully typed.

> **0.x release.** The public API is still settling and minor versions may
> contain breaking changes. Pin an exact version if that matters to you.

## Quick start

```python
from fopost import Fopost

client = Fopost(api_key="fp_...")  # or set FOPOST_API_KEY

workspace = client.workspaces.list()[0]
accounts = client.accounts.list(workspace_id=workspace.id)

post = client.posts.create(
    workspace_id=workspace.id,
    content="Hello from Python",
    accounts=[a.id for a in accounts],
)

client.posts.publish(post.id)
```

`content` takes a string for a single block, or a list for a thread:

```python
client.posts.create(
    workspace_id=workspace.id,
    content=[
        "First post in the thread",
        {
            "text": "Second one, with an image",
            "media": [
                {"type": "image", "name": "chart.png", "url": "https://.../chart.png"},
            ],
        },
    ],
    accounts=[a.id for a in accounts],
)
```

## Scheduling

`status` is `"draft"` or `"scheduled"`; a scheduled post needs `schedule_at`. To send something out now, create it and call `publish`.

```python
from datetime import datetime, timezone

client.posts.create(
    workspace_id=workspace.id,
    status="scheduled",
    schedule_at=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
    content="Scheduled with the SDK",
    accounts=[accounts[0].id],
)
```

## Pagination

`posts.list` returns one page and iterates over its items directly. `posts.iter` walks every page for you:

```python
page = client.posts.list(workspace_id=workspace.id, status="published", per_page=50)
print(f"{page.meta.total} published posts")
for post in page:
    print(post.id, post.status)

# Every post, one page fetched at a time
for post in client.posts.iter(workspace_id=workspace.id):
    print(post.id)

# Or page by page, when you want the meta
for page in client.posts.iter_pages(workspace_id=workspace.id):
    print(page.meta.current_page, len(page))
```

## AI features

```python
balance = client.ai.credits()
print(f"{balance.credits_remaining} of {balance.credits_total} credits left")

result = client.ai.generate_caption(
    current_caption="shipping a new feature",
    platforms=["twitter", "linkedin"],
)
print(result.caption)
```

`rewrite` and `repurpose_url` are wired the same way:

```python
rewrites = client.ai.rewrite(
    content="Long article-style draft...",
    platforms=["twitter", "linkedin", "bluesky"],
)
for variant in rewrites.results:
    print(variant.platform, variant.content)

repurposed = client.ai.repurpose_url(
    url="https://example.com/blog/post",
    platforms=["twitter", "linkedin", "bluesky", "threads"],
)
```

> **API keys reach `credits` and `generate_caption`.** `rewrite` and
> `repurpose_url` currently require a signed-in dashboard session and answer
> `401` to an API key. They are here so the surface is complete once the server
> opens them up.

## Blog

`client.blog` plans keywords, writes articles and publishes them to a website. A post goes
to a social network; an article goes to a website. `suggest_seeds` proposes search terms from
the blog `goal` and topics, `plan_keywords` researches them into `suggested` keywords, and
setting a keyword's status to `planned` puts it on the calendar. A draft is submitted for
approval before it can be published.

```python
article = client.blog.request_article(
    workspace.id,
    keyword="best trail running shoes",
    instructions="Mention the return policy.",
)
print(article.status)  # "queued"; it becomes a draft once written

for draft in client.blog.list_articles(workspace.id, status="draft"):
    client.blog.submit_article(workspace.id, draft.id)
    client.blog.publish_article(workspace.id, draft.id)
```

With the Website target, every published article is POSTed to your `website_url` as a signed
webhook. `verify_webhook` checks the signature over the raw body and returns the envelope:

```python
from fopost import ArticlePublishedPayload, verify_webhook


@app.post("/webhooks/fopost")
async def inbound(request: Request) -> Response:
    secret = os.environ["FOPOST_WEBHOOK_SECRET"]
    event = verify_webhook(await request.body(), request.headers, secret)
    if event.event == "article.published":
        article = ArticlePublishedPayload.model_validate(event.data)
        save_article(article.slug, article.body_html)
    return Response(status_code=204)
```

The secret is returned once, when `update_settings(..., website_url=...)` first saves the URL;
`rotate_website_secret` issues a new one. A forged, stale or unsigned delivery raises
`WebhookVerificationError` with a `code`.

## Analytics

```python
# How long a post keeps earning, from the repeated readings of each post
decay = client.analytics.decay(days=30)
print(decay.half_life_bucket)  # e.g. "1h_3h"

# Whether posting more earned more
cadence = client.analytics.frequency(days=90)
print(cadence.best.label if cadence.best else None)  # e.g. "3-5 a week"

# Every reading held for one post, with what moved between them
timeline = client.analytics.timeline(post.id)

# Mirror the metrics into your own store, without refetching everything
cursor = None
while True:
    page = client.analytics.changes(since=cursor)
    save(page.changes)
    if not page.has_more or page.cursor is None:
        break
    cursor = page.cursor.isoformat()

# Refresh one post now instead of waiting for the next collection run
client.analytics.collect_post(post.id)

# Posts on the account that never went out through FoPost
for native in client.analytics.native_posts(accounts[0].id):
    print(native.permalink, native.metrics.engagements)
```

A post is addressed by its FoPost id or by its permalink, so a post made by
hand on the network works the same way::

    client.analytics.timeline("https://x.com/acme/status/1")

## Direct uploads

`upload_direct` presigns an upload slot, PUTs the bytes straight to storage, and
registers the result as a library item:

```python
with open("chart.png", "rb") as f:
    item = client.media.upload_direct(
        workspace_id=workspace.id,
        filename="chart.png",
        mime_type="image/png",
        data=f.read(),
    )
print(item.id, item.preview_url)
```

`presign` and `complete` are the two halves, for when you want to send the bytes
yourself. Both take the optional `folder_id`, `origin`, `brand_role`, `brand_voice_id`
and `person_consent` fields the library accepts.

### Upload limits

`media.limits` reports what the account may upload. `max_file_bytes` is the ceiling for
any route (it grows with the number of connected accounts, or with the Large Uploads
add-on); `multipart_max_file_bytes` is the most one multipart request may carry per
file, above which a file needs `upload_direct`:

```python
limits = client.media.limits(workspace_id=workspace.id)
print(limits.max_file_bytes, limits.multipart_max_file_bytes, limits.next_tier)
```

A file over the ceiling raises `FileTooLargeError` (HTTP 413, `error == "file_too_large"`)
with `max_file_bytes`, `file_bytes` and `upgrade_url` readable on the error.

## Files on posts

`posts.create` and `posts.update` take `files`: paths, open binary files, or
`(filename, bytes, mime_type)` tuples. They are stored in the workspace library and
attached to the first content block:

```python
post = client.posts.create(
    workspace_id=workspace.id,
    content="Launch day",
    accounts=[a.id for a in accounts],
    files=["launch.png", ("clip.mp4", clip_bytes, "video/mp4")],
)
```

The SDK picks the route: when every file fits in a multipart request it sends one, and
otherwise it uploads each file directly and attaches the results before sending the
post. On `update` with no `content`, the files are appended to the post's first block.

## Configuration

```python
Fopost(
    api_key="fp_...",  # or FOPOST_API_KEY
    base_url="https://api.fopost.com/v1",  # override for a dev server
    timeout=30.0,  # seconds, or an httpx.Timeout
    max_retries=3,  # total attempts on a 429
    http_client=my_httpx_client,  # bring your own transport
)
```

| Env var            | Used for                                     |
| ------------------ | -------------------------------------------- |
| `FOPOST_API_KEY` | API key, when not passed to the constructor  |

The client is a context manager, and closes its transport on exit:

```python
with Fopost() as client:
    client.posts.list(workspace_id=workspace.id)
```

A `429` is retried automatically, waiting for the interval the API asks for in
`Retry-After` (delta-seconds or an HTTP date, capped at 60s). `max_retries`
counts total attempts, so the default of 3 means two retries.

## Error handling

Every non-2xx response raises `FopostError` or one of its subclasses, carrying
the API's `status`, `code`, and `message`.

```python
from fopost import Fopost, FopostError, PaymentRequiredError, RateLimitError

try:
    client.posts.publish("9b2f6c1e-...")
except PaymentRequiredError as err:
    print(f"Out of credits — upgrade at {err.upgrade_url}")
except RateLimitError as err:
    print(f"Rate limited, retry in {err.retry_after}s")
except FopostError as err:
    print(f"API {err.status} ({err.code}): {err.message}")
```

| Status | Exception               |
| ------ | ----------------------- |
| 401    | `AuthenticationError`   |
| 402    | `PaymentRequiredError`  |
| 403    | `PermissionDeniedError` |
| 404    | `NotFoundError`         |
| 429    | `RateLimitError`        |
| other  | `FopostError`         |

## Resources

| Namespace    | Methods                                                                                |
| ------------ | -------------------------------------------------------------------------------------- |
| `posts`      | `list`, `iter`, `iter_pages`, `get`, `create`, `update`, `delete`, `publish`, `cancel`, `retry`, `preflight`, `unpublish`, `deliveries`, `validate_bulk_import`, `commit_bulk_import`, `rollback_bulk_import` |
| `accounts`   | `list`, `get`, `health`, `update`, `move`, `toggle_primary`, `validate_credentials`, `refresh_token`, `create_telegram_connect_code`, `get_telegram_connect_status`, `get_telegram_bot_commands`, `set_telegram_bot_commands`, `delete_telegram_bot_commands`, `list_slack_channels`, `list_slack_members`, `get_slack_identity`, `update_slack_identity`, `list_communities`, `sync_communities`, `search_communities`, `add_community`, `remove_community`, `list_reddit_subreddits`, `list_reddit_subreddit_rules`, `list_reddit_flairs`, `set_reddit_default_subreddit`, `follow_x_user`, `unfollow_x_user`, `get_x_post`, `search_x_posts`, `get_ice_breakers`, `set_ice_breakers`, `delete_ice_breakers`, `get_persistent_menu`, `set_persistent_menu`, `delete_persistent_menu`, `get_greeting`, `set_greeting`, `delete_greeting`, `get_webhook_subscription`, `resubscribe_webhook`, `list_discord_channels`, `switch_discord_channel`, `get_discord_identity`, `update_discord_identity`, `list_discord_pins`, `delete_discord_message`, `pin_discord_message`, `unpin_discord_message`, `crosspost_discord_message`, `create_discord_thread`, `send_discord_dm`, `list_discord_events`, `get_discord_event`, `create_discord_event`, `update_discord_event`, `delete_discord_event`, `list_discord_members`, `get_discord_member`, `list_discord_roles`, `create_discord_role`, `update_discord_role`, `delete_discord_role`, `add_discord_member_role`, `remove_discord_member_role`, `platform_metrics` |
| `account_groups` | `list`, `create`, `get`, `update`, `delete`, `set_members`                         |
| `workspaces` | `list`, `get`, `create`, `update`, `delete`                                            |
| `labels`     | `list`, `create`, `get`, `update`, `delete`                                            |
| `media`      | `list`, `upload`, `delete`, `limits`, `presign`, `complete`, `upload_direct`           |
| `ai`         | `credits`, `generate_caption`, `rewrite`, `repurpose_url`                              |
| `inbox`      | `list`, `threads`, `conversations`, `unread_count`, `accounts`, `platforms`, `mark_thread_read`, `refresh`, `update`, `edit_comment`, `reply`, `hide`, `unhide`, `delete`, `like`, `unlike`, `repost`, `unrepost`, `bookmark`, `unbookmark`, `vote`, `pin`, `unpin`, `react`, `start_conversation`, `set_typing`, `handover`, `list_approvals`, `approve_reply`, `reject_reply` |
| `inbox`      | `list`, `threads`, `conversations`, `unread_count`, `accounts`, `platforms`, `mark_thread_read`, `refresh`, `update`, `edit_comment`, `reply`, `hide`, `unhide`, `delete`, `like`, `unlike`, `repost`, `unrepost`, `bookmark`, `unbookmark`, `vote`, `pin`, `unpin`, `react`, `start_conversation`, `set_typing`, `list_approvals`, `approve_reply`, `reject_reply` |
| `contacts`   | `list`, `get`, `create`, `update`, `delete`, `conversations`, `import_csv`, `list_fields`, `create_field`, `update_field`, `delete_field`, `conversation_analytics` |
| `broadcasts` | `list`, `get`, `create`, `update`, `delete`, `send`, `cancel`, `recipients` |
| `sequences`  | `list`, `get`, `create`, `update`, `delete`, `enroll`, `unenroll`, `enrollments` |
| `ads`        | `list`, `external`, `boostable`, `connections`, `sources`, `providers`, `authorize`, `delete_connection`, `boost`, `create`, `refresh`, `set_status`, `delete`, `audiences`, `create_audience`, `search_targeting`, `lead_forms`, `create_lead_form`, `leads`, `account_tree`, `create_campaign`, `get_campaign`, `update_campaign`, `delete_campaign`, `duplicate_campaign`, `create_ad_set`, `get_ad_set`, `update_ad_set`, `delete_ad_set`, `duplicate_ad_set`, `create_network_ad`, `get_network_ad`, `update_network_ad`, `delete_network_ad`, `duplicate_network_ad`, `bulk_set_status`, `creatives`, `create_creative`, `get_creative`, `delete_creative`, `get_audience`, `update_audience`, `delete_audience`, `add_audience_users`, `add_audience_companies`, `estimate_reach`, `insights`, `ad_insights`, `get_lead_form`, `archive_lead_form`, `leads_feed`, `lead_pages`, `subscribe_lead_page`, `unsubscribe_lead_page`, `goals`, `catalogs`, `create_catalog`, `get_catalog`, `update_catalog`, `delete_catalog`, `catalog_products`, `write_catalog_products`, `product_feeds`, `create_product_feed`, `delete_product_feed`, `feed_uploads`, `start_feed_upload`, `product_sets`, `create_product_set`, `update_product_set`, `delete_product_set`, `reach_frequency`, `create_reach_frequency`, `get_reach_frequency`, `reserve_reach_frequency`, `cancel_reach_frequency`, `library`, `partnership_creators`, `request_partnership`, `revoke_partnership`, `account_activity`, `labels`, `create_label`, `update_label`, `delete_label`, `apply_label`, `studies`, `create_study`, `get_study`, `delete_study`, `ios_campaign_limits`, `high_demand_periods`, `create_high_demand_period`, `delete_high_demand_period`, `value_rule_sets`, `create_value_rule_set`, `delete_value_rule_set`, `bid_pricing`, `supply_forecast`, `conversion_rules`, `create_conversion_rule`, `get_conversion_rule`, `update_conversion_rule`, `delete_conversion_rule`, `attach_conversion_rule`, `detach_conversion_rule`, `conversion_metrics`, `send_conversion_events`, `upload_conversions`, `send_conversions`, `conversion_batches`, `pixels`, `create_pixel`, `get_pixel`, `update_pixel`, `share_pixel`, `pixel_stats`, `event_match_quality`, `custom_conversions`, `create_custom_conversion`, `get_custom_conversion`, `update_custom_conversion`, `delete_custom_conversion` |
| `knowledge`  | `list`, `create`, `update`, `delete`, `sync`, `search` |
| `ads`        | `list`, `external`, `boostable`, `connections`, `sources`, `providers`, `authorize`, `delete_connection`, `boost`, `create`, `refresh`, `set_status`, `delete`, `audiences`, `create_audience`, `search_targeting`, `lead_forms`, `create_lead_form`, `leads`, `account_tree`, `create_campaign`, `get_campaign`, `update_campaign`, `delete_campaign`, `duplicate_campaign`, `create_ad_set`, `get_ad_set`, `update_ad_set`, `delete_ad_set`, `duplicate_ad_set`, `create_network_ad`, `get_network_ad`, `update_network_ad`, `delete_network_ad`, `duplicate_network_ad`, `bulk_set_status`, `creatives`, `create_creative`, `get_creative`, `delete_creative`, `get_audience`, `update_audience`, `delete_audience`, `add_audience_users`, `add_audience_companies`, `estimate_reach`, `insights`, `ad_insights`, `get_lead_form`, `archive_lead_form`, `leads_feed`, `lead_pages`, `subscribe_lead_page`, `unsubscribe_lead_page`, `bid_pricing`, `supply_forecast`, `conversion_rules`, `create_conversion_rule`, `get_conversion_rule`, `update_conversion_rule`, `delete_conversion_rule`, `attach_conversion_rule`, `detach_conversion_rule`, `conversion_metrics`, `send_conversion_events`, `upload_conversions`, `send_conversions`, `conversion_batches`, `pixels`, `create_pixel`, `get_pixel`, `update_pixel`, `share_pixel`, `pixel_stats`, `event_match_quality`, `custom_conversions`, `create_custom_conversion`, `get_custom_conversion`, `update_custom_conversion`, `delete_custom_conversion` |
| `google_business` | `get_location`, `update_location`, `get_attributes`, `update_attributes`, `get_menus`, `replace_menus`, `get_services`, `replace_services`, `list_media`, `add_media`, `delete_media`, `list_place_actions`, `create_place_action`, `update_place_action`, `delete_place_action`, `get_verification_options`, `start_verification`, `complete_verification`, `get_performance`, `get_search_keywords`, `assign` |
| `blog`       | `get_settings`, `update_settings`, `rotate_website_secret`, `test_website`, `list_keywords`, `suggest_seeds`, `plan_keywords`, `add_keyword`, `update_keyword`, `delete_keyword`, `list_articles`, `request_article`, `get_article`, `update_article`, `regenerate_article`, `submit_article`, `publish_article`, `reject_article`, `delete_article` |
| `blogs`      | `list_blogs`, `list_articles`, `get_article`, `create_article`, `update_article`, `delete_article`, `list_products`, `update_product` |
| `validate`   | `post`, `length`, `media`, `subreddit` |
| `whatsapp`   | `get_profile`, `update_profile`, `request_display_name`, `set_username`, `list_templates`, `list_template_library`, `get_template`, `create_template`, `import_template`, `update_template`, `delete_template`, `list_groups`, `create_group`, `get_group`, `update_group`, `delete_group`, `get_group_invite_link`, `reset_group_invite_link`, `remove_group_participants`, `list_blocked`, `block_users`, `unblock_users`, `get_commerce_settings`, `update_commerce_settings`, `link_catalog`, `list_flows`, `get_flow`, `create_flow`, `update_flow`, `delete_flow`, `upload_flow_json`, `publish_flow`, `deprecate_flow`, `list_flow_responses`, `get_encryption_key_status`, `set_encryption_key`, `get_account_events`, `list_sandbox_sessions`, `create_sandbox_session` |
| `analytics`  | `overview`, `time_series`, `top_posts`, `labels`, `posts_table`, `posting_streak`, `demographics`, `inbox`, `collect`, `decay`, `frequency`, `timeline`, `changes`, `collect_post`, `native_posts` |
| `activity`   | `list` |
| `queue`      | `list_slots`, `create_slot`, `update_slot`, `delete_slot`, `next`, `preview` |
| `connect_sessions` | `create`, `get` |
| `webhook_endpoints` | `list`, `create`, `update`, `delete`, `test`, `deliveries`, `get_delivery`, `redeliver` |
| `automations` | `list`, `create`, `get`, `update`, `delete`, `toggle`, `stats`, `versions`, `get_version`, `restore_version`, `runs`, `get_run` |
| `logs`       | `list` |

For an endpoint the SDK does not wrap yet, `client.request` sends an
authenticated call and hands back the decoded body:

```python
client.request("GET", "/analytics/summary", params={"workspace_id": workspace.id})
```

## Chat adapter

`fopost.chat_adapter` wraps the inbox conversation and reply endpoints in a send/receive
interface, so a chatbot framework can treat FoPost as one channel across every network
that carries direct messages.

```python
from fopost import Fopost
from fopost.chat_adapter import ChatAdapter

chat = ChatAdapter(
    Fopost(api_key=os.environ["FOPOST_API_KEY"]),
    workspace_id=workspace_id,
    webhook_secret=os.environ["FOPOST_WEBHOOK_SECRET"],
)
```

**Inbound** is the `inbox.message_received` webhook. Subscribe an endpoint to it in FoPost,
then hand the raw body and the request headers to `parse_webhook`. It verifies the
signature, refuses a replay, and returns the event; the event carries ids only, so
`receive_one` reads the text back:

```python
@app.post("/webhooks/fopost")
async def inbound(request: Request) -> Response:
    event = chat.parse_webhook(await request.body(), request.headers)
    message = chat.receive_one(event)
    if message is None:
        return Response(status_code=204)

    chat.typing(message.conversation_id, message.account_id)
    chat.send(reply_to=message.id, text=your_bot(message.text))
    chat.mark_read(message)
    return Response(status_code=204)
```

No webhook? `receive()` polls the same thing:

```python
for message in chat.receive():
    chat.send(reply_to=message.id, text=your_bot(message.text))
    chat.mark_read(message)
```

**Outbound** takes one of three shapes. Reply to a message, reply into a thread, or open
one by handle:

```python
chat.send(reply_to=message.id, text="On it.")
chat.send(conversation_id="conv_...", text="Still here.")
chat.send(account_id="acc_...", handle="samrivera", text="Following up.")
```

| Method | What it does |
| ------ | ------------ |
| `parse_webhook(body, headers)` | Verifies a delivery and returns the `ChatEvent` |
| `verify_webhook(body, headers)` | Signature check on its own; raises on a forged or stale delivery |
| `receive(...)` | Inbound DMs, unread by default |
| `receive_one(event_or_id)` | The full message behind an event id, or `None` |
| `send(...)` | Reply, reply into a thread, or open one |
| `typing(conversation_id, account_id, on=True)` | Typing indicator |
| `mark_read(message)` | Marks the message read |

Sending needs the `publish` scope on top of `inbox`. Every failure is a `ChatAdapterError`
with a `code` (`invalid_signature`, `stale_delivery`, `unexpected_event`,
`unsupported_target`, and the rest) or the usual `FopostError` from the API.

## Example

[`examples/create_post.py`](examples/create_post.py) creates a post against a
running API:

```bash
export FOPOST_API_KEY=fp_...
export FOPOST_BASE_URL=http://localhost:8080/v1
python examples/create_post.py "Hello from the Python SDK" --publish
```

## Contributing

Issues and pull requests are welcome at
[fopost/fopost-python](https://github.com/fopost/fopost-python).

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run mypy
```

## License

MIT

Questions or a problem: [fopost.com/contact](https://fopost.com/contact).

### Google Ads

Campaigns, ad groups, ads, audiences and insights are on `client.ads` and dispatch by
connection. What only Google has is under `client.ads.google`:

```python
keywords = client.ads.google.keywords(
    connection_id="c4d5e6f7-…",
    customer_id="1234567890",
)

client.ads.google.create_keyword(
    workspace_id="7d2b8c11-…",
    connection_id="c4d5e6f7-…",
    customer_id="1234567890",
    ad_group_id="1234567890~adGroup~77",
    text="running shoes",
    match_type="EXACT",
)
```

Also `keyword_ideas`, `keyword_metrics`, `search_terms`, `bid_strategies`,
`ad_schedule` and `set_ad_schedule`, the negative keyword lists, `assets` and
`asset_groups`, `local_services_leads`, the conversion methods, and `query` for a raw
read-only GAQL SELECT. Changes need the `publish` scope as well as `ads`; `customer_id`
has to name an account the connection's grant reaches.
