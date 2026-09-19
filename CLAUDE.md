# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What This Is

`fopost` on PyPI — the official Python client for the FoPost REST API (`fopost.com`).
Current version `0.3.0`. It wraps the API's HTTP surface in a namespaced client
(`posts`, `accounts`, `account_groups`, `workspaces`, `labels`, `ai`, `inbox`, `ads`) returning pydantic v2 models.

Requires Python >= 3.10 (CI matrix: 3.10–3.13). Runtime deps: `httpx>=0.27`,
`pydantic>=2.7`. Built with hatchling from `src/fopost`, ships `py.typed`.

## Downstream Packages

These repos wrap this SDK and must be updated in lockstep:

- `fopost-django` — Django integration for the FoPost API
- `fopost-fastapi` — FastAPI integration for the FoPost API

**Whenever you change this SDK's public surface — a renamed method, a changed parameter,
a new or removed resource, a new error type, a bumped minimum language version — you must
open a matching PR in every repo listed above in the same session.** They are separate
git repos, checked out as siblings at `../fopost-<child>`. A parent release that silently
breaks a child is only discovered by the user who upgrades first.

Also bump the child's dependency constraint on this package and note the change in its
CHANGELOG when this package is released.

## Brand Rules

- The product is **FoPost** (`fopost.com`). Never write "OwlStack" — retired Aug 2026.
- Never write an email address. Support is https://fopost.com/contact and GitHub issues.
- Never name AI providers/models, infrastructure vendors, or any person. `client.ai`
  returns captions, rewrites, and credit counts — never a model name.
- Never type a platform count. The README and package description say "+30 social
  platforms"; keep it that way. `models.PLATFORMS` is a tuple of slugs, not a number to quote.

## Architecture

```
src/fopost/
  __init__.py       public exports, __version__ from importlib.metadata, FoPost alias
  client.py         Fopost — namespaces, escape hatch, context manager
  _http.py          HttpClient: headers, retry loop, decode, unwrap()
  errors.py         FopostError + subclasses + error_from_response()
  models.py         pydantic models, PLATFORMS, POST_STATUSES, Page/PageMeta
  resources/        _base.py (Resource, parse_list, UNSET, drop_unset)
                    posts.py accounts.py account_groups.py workspaces.py labels.py ai.py
                    inbox.py ads.py
```

Request flow: a resource method builds a snake_case body/params dict, calls
`self._http.get/post/put/delete(...)` → `HttpClient.request()` (retry loop) →
`HttpClient._decode()` (raises or returns the parsed body) → back in the resource,
`unwrap(body)` peels `{"data": ...}` and `Model.model_validate(...)` types it.

**The envelope unwrap lives in the resources, not the transport.** `_http.unwrap()` is a
free function the resources call; `HttpClient` hands back the whole decoded body so the
escape hatch and paginated readers can see `meta`.

`Fopost` owns its `httpx.Client` unless one is injected, closes it in `close()`, and works
as a context manager. `FoPost` is exported as an alias for people arriving from the
TypeScript SDK.

## API Contract

- Base URL: `https://api.fopost.com/v1` (`DEFAULT_BASE_URL`), the same path the Go and Rust
  SDKs use and the one the docs publish. `/api/v1` is **not** served and returns 404 — never
  reintroduce it. Override with `Fopost(base_url=...)`; there is no `FOPOST_BASE_URL` env
  read.
- Auth: header `X-API-Key`. `api_key` falls back to the `FOPOST_API_KEY` environment
  variable; missing on both raises `ValueError`.
- Headers sent on every request: `Accept: application/json`,
  `Content-Type: application/json`, `X-API-Key`, `User-Agent: fopost-python` (no version
  suffix).
- Timeout: 30s default (`DEFAULT_TIMEOUT`), passed to `httpx.Client`.
- **Retries: 429 only.** `max_retries=3` counts *total attempts*, so two retries. The wait
  is `Retry-After` when present — parsed as delta-seconds *or* an HTTP date — otherwise
  `1.0` second, capped at 60s. There is **no exponential backoff**, and **5xx and network
  errors are not retried** (`tests/test_retry.py::test_other_statuses_are_not_retried`
  pins this). This diverges from the shared SDK brief, which asks for 5xx + network retry
  with `500ms * 2^(attempt-1)` backoff.
- Success envelope: `unwrap()` peels `{"data": ...}` whenever a `data` key is present.
  Paginated lists come back as `Page[T]` with `PageMeta` (`current_page`, `per_page`,
  `total`, `last_page`, `from_`, `to`).
- Error envelope: `{"error": "<code>", "message": "<text>"}` → `FopostError.code` /
  `.message`, with `.status` and the raw `.body`. Subclasses:
  `AuthenticationError` (401), `PaymentRequiredError` (402, `.upgrade_url` read off the
  body), `PermissionDeniedError` (403), `NotFoundError` (404), `RateLimitError` (429,
  `.retry_after` in seconds). **There is no Validation (400/422) or Server (5xx)
  subclass** — those raise the base `FopostError`.
- Rate-limit headers (`X-RateLimit-*`) are **not surfaced**. Only the Go SDK reads them.
- Escape hatch: `client.request(method, path, json=..., params=...)` returns the decoded
  body with no unwrap and no model parsing.

Resource coverage is a subset of the API: posts (list/iter/iter_pages/get/create/update/
delete/publish/cancel/retry/preflight/deliveries), accounts (list/get/health/update/move),
account_groups (list/create/get/update/delete/set_members), workspaces
(list/get), labels (list), ai (credits/generate_caption/rewrite/repurpose_url), inbox (the `/v1/inbox`
family except the X Chat routes), ads (the `/v1/ads` family), validate (post/length/media). `communities`, `webhooks`,
`analytics`, `automations`, and `media` are **not wrapped here** — the Go and Rust SDKs have
them. Adding one is a public-surface change: see the Downstream Packages rule.

## Commands

The project uses `uv` (CI installs it via `astral-sh/setup-uv`).

```bash
uv sync --group dev              # install runtime + dev deps
uv run pytest                    # offline test suite (-q via pyproject)
uv run ruff check .              # lint
uv run ruff format --check .     # format check (use `ruff format .` to fix)
uv run mypy                      # strict, files = src/fopost
uv build                         # sdist + wheel into dist/
```

`.github/workflows/ci.yml` runs ruff check, ruff format --check, mypy, and pytest across
Python 3.10/3.11/3.12/3.13 on push to `main`, on PRs, and on dispatch. All four must pass.

## Conventions

- Ruff: line length 100, rules `E, F, I, UP, B`; isort first-party `fopost`, `tests`.
- Mypy `strict = true` over `src/fopost` (tests are not type-checked).
- `from __future__ import annotations` at the top of every module.
- Public API is snake_case keyword-only where it reads better (`list(*, workspace_id=...)`).
- Models subclass `FopostModel`: field aliases via `AliasChoices` accept both the
  snake_case and camelCase spellings the API mixes, `extra="allow"` keeps unknown keys so a
  server-side addition never breaks a client. Enum-ish fields stay plain `str` with a
  `PLATFORMS`/`POST_STATUSES` tuple beside them for the same reason.
- Partial updates use the `UNSET` sentinel from `resources/_base.py` plus `drop_unset()`,
  so a `PUT` only sends what the caller passed. Do not use `None` as "not provided".
- Docstrings on public classes and non-obvious methods. No narrated docblocks on obvious
  code; short one-line `why` comments where needed.
- Internal helpers are `_`-prefixed and are not re-exported from `__init__`.

## Testing

`pytest` + `respx` (which mocks `httpx` at the transport layer). **Tests never hit the
live API** — every request is routed to `https://api.test.fopost.com/v1` and matched by
a `respx` route.

`tests/conftest.py` provides:
- `client` — a `Fopost` bound to `BASE_URL` inside a context manager
- `no_sleep` — monkeypatches `fopost._http._sleep` and records the waits, so retry tests
  assert on backoff without sleeping. `_sleep` is indirected in `_http.py` for this reason;
  keep the indirection.
- Fixture dicts (`POST_FIXTURE`, `ACCOUNT_FIXTURE`, `WORKSPACE_FIXTURE`, `LABEL_FIXTURE`)
  deliberately mixing snake_case and camelCase, matching what the API actually sends.

Cover at minimum, for anything new: the auth header is sent, retry/no-retry behaviour,
error mapping, and one happy path per resource.

## Releasing

Tag `v<version>` matching `pyproject.toml`; `.github/workflows/release.yml` publishes to
PyPI. It verifies the tag equals the project version, re-runs ruff/mypy/pytest, builds,
then installs the built wheel into a scratch venv and imports `Fopost` with every namespace
bound (this catches a wheel that builds but is unimportable). Publishing is `skip-existing`.

**No repo secret is used.** Publishing goes through **PyPI trusted publishing** (OIDC,
`pypa/gh-action-pypi-publish@release/v1`, `id-token: write`) and is gated behind the
GitHub environment named `pypi`. Before the first tag, the trusted publisher for
`fopost/fopost-python` must be configured on PyPI — otherwise the publish step fails with
no token to fall back on.

## Git

Conventional Commits (`<type>(<scope>): <description>`), atomic — one logical change per
commit. Branch `feature/<description>` off a fresh `main`, merge via PR.
Never `gh pr create` — push the branch and hand over the compare link
(`https://github.com/fopost/fopost-python/compare/main...<branch>`).
