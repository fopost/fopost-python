# Changelog

All notable changes to `fopost` are documented here.

## 0.4.0 - 2026-10-18

### Added

- `client.queue`: `list_slots`, `create_slot`, `update_slot`, `delete_slot`, `next` and
  `preview` for the posting queue, and `schedule="queue"` on `posts.create` and `posts.update`
  to take the next free slot instead of a `schedule_at`.
- `client.connect_sessions`: `create` and `get` for hosted connect links (`ConnectSession`).
- `client.webhook_endpoints`: `list`, `create`, `update`, `delete`, `test`, `deliveries`,
  `get_delivery` and `redeliver` (`WebhookEndpoint`, `WebhookDelivery`, `WEBHOOK_EVENTS`). The
  name is deliberately not `webhooks`, which stays the signature-verification module.
- `client.automations`: `list`, `create`, `get`, `update`, `delete`, `toggle`, `stats`,
  `versions`, `get_version`, `restore_version`, `runs` and `get_run` (`Automation`,
  `AutomationVersion`, `AutomationRun`, `AutomationStats`, `AUTOMATION_TRIGGER_TYPES`).
- `client.logs.list` for the request log, with `meta.next_cursor` and `summary`
  (`RequestLogPage`).
- `posts.unpublish` (`UnpublishResult`) and bulk import: `posts.validate_bulk_import`,
  `posts.commit_bulk_import`, `posts.rollback_bulk_import`.
- `workspaces.create`, `workspaces.update`, `workspaces.delete`; `labels.create`, `labels.get`,
  `labels.update`, `labels.delete`.
- `accounts.toggle_primary`, `accounts.validate_credentials` and `accounts.refresh_token`
  (`AccountPrimary`, `AccountValidation`, `AccountTokenRefresh`).
- `accounts.list_communities`, `sync_communities`, `search_communities`, `add_community` and
  `remove_community` for X communities (`Community`, `CommunitySearchResult`).
- `media.list`, `media.upload` (multipart, up to 5 files) and `media.delete`; `MediaItem` carries
  the library-row fields (`workspace_id`, `mime_type`, `tags`, `folder_id`, `brand_role`, …).
- `analytics.overview`, `time_series`, `top_posts`, `labels`, `posts_table`, `posting_streak`,
  `demographics`, `inbox` and `collect`, typed as `AnalyticsOverview`, `AnalyticsTimeSeries`,
  `TopPost`, `LabelAnalytics`, `PostsTable`, `PostingStreakDay`, `AudienceDemographics`,
  `InboxAnalytics` and `AnalyticsCollectResult`.
- `Workspace.connect_redirect_domains` and `updated_at`; `Label.created_at` and `updated_at`.

## 0.3.0 - 2026-10-18

### Removed

- **Breaking:** `BlogSettings.auto_publish` and the `auto_publish` argument of
  `blog.update_settings` are gone. Nothing publishes without approval: a draft goes to
  `in_review` through `blog.submit_article` first.

### Added

- `accounts.list_reddit_subreddits`, `accounts.list_reddit_subreddit_rules`,
  `accounts.list_reddit_flairs` and `accounts.set_reddit_default_subreddit` for Reddit
  destinations (a flair id is valid only in its subreddit; `None` as the default falls back
  to the profile page), `validate.subreddit(account_id=..., name=...)` returning a
  `SubredditCheck` before a post exists, and `inbox.vote(item_id, direction)` with
  `"up"`, `"down"` or `"none"` to take a vote back. `SocialAccount.reconnect_required` and
  the inbox item's `vote` and `can_vote` are new fields.
- `client.blogs`: `list_blogs`, `list_articles`, `get_article`, `create_article`,
  `update_article`, `delete_article`, `list_products` and `update_product` reach the blogs,
  articles and products already on a connected site, addressed by the platform's own ids
  (`RemoteBlog`, `RemoteArticle`, `RemoteProduct`). `update_article` edits the live article
  in place and sends only the arguments passed. Reads need the `posts` scope, writes `publish`.
- `blog.suggest_seeds(workspace_id, seeds=None, prompt=None)` returns about 10 search terms
  from the blog goal and topics (`ai` scope; an empty balance raises `PaymentRequiredError`).
- `blog.submit_article` moves a draft, failed or rejected article to `in_review` (`posts`
  scope, 409 from any other state). `publish_article` and `publish_at` now need an article
  in review, so a draft is a 409 until it is submitted.
- `BlogSettings` carries `goal`, `focus_topics`, `avoid_topics` and `plan_run` (a
  `BlogPlanRun`), and `blog.update_settings` takes `goal`, `focus_topics` and `avoid_topics`.
  `BlogKeyword.fit_reason`, `BLOG_GOALS`, and `in_review` in `BLOG_ARTICLE_STATUSES`.
  `plan_keywords` no longer fills the calendar: setting a keyword to `planned` picks it, and
  `review_hold_days` is how many days before its date it starts being written.
- `media.limits(workspace_id=None)` returns an `UploadLimits` model: `max_file_bytes`,
  `multipart_max_file_bytes`, `max_files_per_upload`, `next_tier`, `allowed_types` and the
  source of the ceiling.
- `posts.create` and `posts.update` take `files` (paths, open binary files, or
  `(filename, bytes, mime_type)` tuples). Files that fit a multipart request go in one
  request to the post endpoint; larger files are uploaded directly and attached to the
  first content block.
- `media.presign` and `media.upload_direct` accept `folder_id`, `origin`, `brand_role`,
  `brand_voice_id` and `person_consent`. `PresignedUpload.max_file_bytes` reports the
  ceiling the slot was issued under.
- `FileTooLargeError` for HTTP 413 `file_too_large`, with `max_file_bytes`, `file_bytes`
  and `upgrade_url`.
- `client.blog`: settings, keyword planning and articles under `/v1/blog`, with the
  `BlogSettings`, `BlogKeyword`, `BlogArticle`, `BlogArticleFull` and `BlogArticleImage` models.
  The workspace travels as `workspace_id` on the query string; `test_website` returns the
  site's `http_status`.
- `fopost.webhooks.verify` (also exported as `verify_webhook`): verifies any FoPost webhook
  delivery over the raw body and returns the `{event, data, timestamp}` envelope, with the
  typed `ArticlePublishedPayload` for `article.published`.

### Changed

- Presign accepts files up to 5 GB; the limit now depends on the account rather than a
  fixed size.
- `ChatAdapter.verify_webhook` now runs on the shared `fopost.webhooks` verifier. Behaviour and
  error codes are unchanged.
