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
yourself.

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
| `posts`      | `list`, `iter`, `iter_pages`, `get`, `create`, `update`, `delete`, `publish`, `cancel`, `retry`, `preflight`, `deliveries` |
| `accounts`   | `list`, `get`, `health`, `update`, `move`, `create_telegram_connect_code`, `get_telegram_connect_status`, `get_telegram_bot_commands`, `set_telegram_bot_commands`, `delete_telegram_bot_commands` |
| `account_groups` | `list`, `create`, `get`, `update`, `delete`, `set_members`                         |
| `workspaces` | `list`, `get`                                                                          |
| `labels`     | `list`                                                                                 |
| `media`      | `presign`, `complete`, `upload_direct`                                                 |
| `ai`         | `credits`, `generate_caption`, `rewrite`, `repurpose_url`                              |
| `inbox`      | `list`, `threads`, `conversations`, `unread_count`, `accounts`, `platforms`, `mark_thread_read`, `refresh`, `update`, `edit_comment`, `reply`, `hide`, `unhide`, `delete`, `like`, `unlike`, `pin`, `unpin`, `react`, `start_conversation`, `set_typing`, `list_approvals`, `approve_reply`, `reject_reply` |
| `ads`        | `list`, `external`, `boostable`, `connections`, `sources`, `authorize_meta`, `delete_connection`, `boost`, `create`, `refresh`, `set_status`, `delete`, `audiences`, `create_audience`, `search_targeting`, `lead_forms`, `create_lead_form`, `leads` |
| `validate`   | `post`, `length`, `media` |

For an endpoint the SDK does not wrap yet, `client.request` sends an
authenticated call and hands back the decoded body:

```python
client.request("GET", "/analytics/summary", params={"workspace_id": workspace.id})
```

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
