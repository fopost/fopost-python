# Changelog

All notable changes to `fopost` are documented here.

## Unreleased

### Removed

- **Breaking:** `BlogSettings.auto_publish` and the `auto_publish` argument of
  `blog.update_settings` are gone. Nothing publishes without approval: a draft goes to
  `in_review` through `blog.submit_article` first.

### Added

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
- `fopost.webhooks.verify` (also exported as `verify_webhook`): verifies any FoPost webhook
  delivery over the raw body and returns the `{event, data, timestamp}` envelope, with the
  typed `ArticlePublishedPayload` for `article.published`.

### Changed

- Presign accepts files up to 5 GB; the limit now depends on the account rather than a
  fixed size.
- `ChatAdapter.verify_webhook` now runs on the shared `fopost.webhooks` verifier. Behaviour and
  error codes are unchanged.
