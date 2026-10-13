# Changelog

All notable changes to `fopost` are documented here.

## Unreleased

### Added

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

### Changed

- Presign accepts files up to 5 GB; the limit now depends on the account rather than a
  fixed size.
