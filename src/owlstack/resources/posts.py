"""``client.posts`` — create, schedule, publish, and inspect posts."""

from __future__ import annotations

import builtins
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime
from typing import Any

from .._http import unwrap
from ..models import ContentBlock, Delivery, Page, PageMeta, Post, SocialAccount
from ._base import UNSET, Resource, parse_list

ContentInput = str | Mapping[str, Any] | ContentBlock
AccountInput = str | Mapping[str, Any] | SocialAccount

__all__ = ["PostsResource"]


def _normalize_content(content: str | Sequence[ContentInput]) -> list[dict[str, Any]]:
    """Accept a bare string, one block, or a sequence of blocks."""
    blocks: Sequence[ContentInput]
    if isinstance(content, str):
        blocks = [content]
    elif isinstance(content, (Mapping, ContentBlock)):
        blocks = [content]
    else:
        blocks = list(content)

    out: list[dict[str, Any]] = []
    for block in blocks:
        if isinstance(block, str):
            out.append({"text": block})
        elif isinstance(block, ContentBlock):
            out.append(
                {
                    "text": block.text,
                    "media": [m.model_dump(exclude_none=True) for m in block.media],
                }
            )
        else:
            out.append({k: v for k, v in dict(block).items() if v is not None})
    return out


def _normalize_accounts(accounts: Sequence[AccountInput]) -> list[str]:
    """The API takes bare account ids; also accept account objects or ``{"id": ...}``."""
    out: list[str] = []
    for account in accounts:
        if isinstance(account, str):
            out.append(account)
        elif isinstance(account, SocialAccount):
            out.append(account.id)
        else:
            account_id = dict(account).get("id")
            if not isinstance(account_id, str):
                raise TypeError(f"Cannot read an account id from {account!r}")
            out.append(account_id)
    return out


def _iso(value: str | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return value


class PostsResource(Resource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 30,
        sort: str | None = None,
    ) -> Page[Post]:
        """One page of posts. The result iterates over its items directly."""
        body = self._http.get(
            "/posts",
            {
                "workspace_id": workspace_id,
                "status": status,
                "search": search,
                "page": page,
                "per_page": per_page,
                "sort": sort,
            },
        )
        items = parse_list(Post, body.get("data") if isinstance(body, dict) else body)
        raw_meta = body.get("meta") if isinstance(body, dict) else None
        meta = PageMeta.model_validate(raw_meta) if isinstance(raw_meta, dict) else PageMeta()
        return Page[Post](items=items, meta=meta)

    def iter(
        self,
        *,
        workspace_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        per_page: int = 30,
        sort: str | None = None,
        start_page: int = 1,
    ) -> Iterator[Post]:
        """Walk every matching post, fetching one page at a time."""
        for page in self.iter_pages(
            workspace_id=workspace_id,
            status=status,
            search=search,
            per_page=per_page,
            sort=sort,
            start_page=start_page,
        ):
            yield from page.items

    def iter_pages(
        self,
        *,
        workspace_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        per_page: int = 30,
        sort: str | None = None,
        start_page: int = 1,
    ) -> Iterator[Page[Post]]:
        """Same walk as ``iter``, but yields whole pages so meta stays reachable."""
        page_number = start_page
        while True:
            page = self.list(
                workspace_id=workspace_id,
                status=status,
                search=search,
                page=page_number,
                per_page=per_page,
                sort=sort,
            )
            if not page.items:
                return
            yield page

            last_page = page.meta.last_page
            if last_page is not None and page_number >= last_page:
                return
            if last_page is None and len(page.items) < per_page:
                return
            page_number += 1

    def get(self, post_id: str) -> Post:
        return Post.model_validate(unwrap(self._http.get(f"/posts/{post_id}")))

    def create(
        self,
        *,
        workspace_id: str,
        content: str | Sequence[ContentInput],
        accounts: Sequence[AccountInput] = (),
        status: str = "draft",
        schedule_at: str | datetime | None = None,
        labels: Sequence[str] | None = None,
        title: str | None = None,
        summary: str | None = None,
        content_type: str | None = None,
        settings: Mapping[str, Mapping[str, Any]] | None = None,
        **extra: Any,
    ) -> Post:
        """Create a draft or a scheduled post.

        ``status`` is ``draft`` or ``scheduled``; a scheduled post needs
        ``schedule_at``. To send a post out now, create it and call
        :meth:`publish`.
        """
        body: dict[str, Any] = {
            "workspace_id": workspace_id,
            "status": status,
            "content": _normalize_content(content),
            "accounts": _normalize_accounts(accounts),
        }
        optional = {
            "schedule_at": _iso(schedule_at),
            "labels": list(labels) if labels is not None else None,
            "title": title,
            "summary": summary,
            "content_type": content_type,
            "settings": dict(settings) if settings is not None else None,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        body.update(extra)
        return Post.model_validate(unwrap(self._http.post("/posts", body)))

    def update(
        self,
        post_id: str,
        *,
        content: str | Sequence[ContentInput] | Any = UNSET,
        accounts: Sequence[AccountInput] | Any = UNSET,
        status: str | Any = UNSET,
        schedule_at: str | datetime | None | Any = UNSET,
        labels: Sequence[str] | Any = UNSET,
        title: str | None | Any = UNSET,
        summary: str | None | Any = UNSET,
        content_type: str | Any = UNSET,
        settings: Mapping[str, Mapping[str, Any]] | Any = UNSET,
        **extra: Any,
    ) -> Post:
        """Partial update — only the fields you pass are sent."""
        body: dict[str, Any] = {}
        if content is not UNSET:
            body["content"] = _normalize_content(content)
        if accounts is not UNSET:
            body["accounts"] = _normalize_accounts(accounts)
        if status is not UNSET:
            body["status"] = status
        if schedule_at is not UNSET:
            body["schedule_at"] = _iso(schedule_at)
        if labels is not UNSET:
            body["labels"] = list(labels)
        if title is not UNSET:
            body["title"] = title
        if summary is not UNSET:
            body["summary"] = summary
        if content_type is not UNSET:
            body["content_type"] = content_type
        if settings is not UNSET:
            body["settings"] = dict(settings)
        body.update(extra)
        return Post.model_validate(unwrap(self._http.put(f"/posts/{post_id}", body)))

    def delete(self, post_id: str) -> None:
        self._http.delete(f"/posts/{post_id}")

    def publish(self, post_id: str) -> dict[str, Any]:
        """Queue the post for immediate delivery to its accounts."""
        return _as_dict(unwrap(self._http.post(f"/posts/{post_id}/publish")))

    def cancel(self, post_id: str) -> dict[str, Any]:
        return _as_dict(unwrap(self._http.post(f"/posts/{post_id}/cancel")))

    def retry(self, post_id: str) -> dict[str, Any]:
        """Retry the deliveries that failed, leaving the successful ones alone."""
        return _as_dict(unwrap(self._http.post(f"/posts/{post_id}/retry")))

    def preflight(self, post_id: str) -> dict[str, Any]:
        """Per-account blockers and advisory content signals, without publishing."""
        return _as_dict(unwrap(self._http.post(f"/posts/{post_id}/preflight")))

    # builtins.list, because `list` is a method on this class.
    def deliveries(self, post_id: str) -> builtins.list[Delivery]:
        return parse_list(Delivery, unwrap(self._http.get(f"/posts/{post_id}/deliveries")))


def _as_dict(body: Any) -> dict[str, Any]:
    return body if isinstance(body, dict) else {"data": body}
