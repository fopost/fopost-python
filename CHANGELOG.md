# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added

- `client.blog`: settings, keyword planning and articles under `/v1/blog`, with the
  `BlogSettings`, `BlogKeyword`, `BlogArticle`, `BlogArticleFull` and `BlogArticleImage` models.
- `fopost.webhooks.verify` (also exported as `verify_webhook`): verifies any FoPost webhook
  delivery over the raw body and returns the `{event, data, timestamp}` envelope, with the
  typed `ArticlePublishedPayload` for `article.published`.

### Changed

- `ChatAdapter.verify_webhook` now runs on the shared `fopost.webhooks` verifier. Behaviour and
  error codes are unchanged.
