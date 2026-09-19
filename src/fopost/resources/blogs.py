"""``client.blogs`` — content a connected site already owns.

Most of this SDK creates content. These calls reach what is already there: the
articles on a WordPress site or a Shopify store's blog, and a Shopify store's
products. Every id below is the **platform's own**, never a FoPost id.

Reads need the ``posts`` scope. Anything that changes the site needs ``posts``
and ``publish``, because a change here is visible to the site's own readers.
"""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from typing import Any

from .._http import unwrap
from ..models import RemoteArticle, RemoteBlog, RemoteProduct
from ._base import Resource, parse_list

__all__ = ["BlogsResource"]


class BlogsResource(Resource):
    def list_blogs(self, account_id: str) -> builtins.list[RemoteBlog]:
        """Blogs the account can write to.

        A Shopify store reports every blog it has; WordPress reports its one
        implicit blog under the id ``default``, so both answer the same shape.
        """
        return parse_list(RemoteBlog, unwrap(self._http.get(f"/accounts/{account_id}/blogs")))

    def list_articles(
        self,
        account_id: str,
        blog_id: str,
        *,
        limit: int | None = None,
        status: str | None = None,
        q: str | None = None,
    ) -> builtins.list[RemoteArticle]:
        """Articles on the blog, newest first, drafts included.

        ``status`` is one of ``published``, ``draft``, ``pending`` or
        ``scheduled``; ``q`` matches the title; ``limit`` is 1 to 50.
        """
        return parse_list(
            RemoteArticle,
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/blogs/{blog_id}/articles",
                    {"limit": limit, "status": status, "q": q},
                )
            ),
        )

    def get_article(self, account_id: str, blog_id: str, article_id: str) -> RemoteArticle:
        """One article in full."""
        return RemoteArticle.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/blogs/{blog_id}/articles/{article_id}"))
        )

    def create_article(
        self,
        account_id: str,
        blog_id: str,
        *,
        title: str,
        body: str,
        excerpt: str | None = None,
        status: str | None = None,
        tags: Sequence[str] | None = None,
        author_name: str | None = None,
        image_url: str | None = None,
    ) -> RemoteArticle:
        """Write a new article to the blog. Needs the ``publish`` scope.

        ``body`` is FoPost body markup; the site's own format is rendered from it.
        """
        payload: dict[str, Any] = {"title": title, "body": body}
        if excerpt is not None:
            payload["excerpt"] = excerpt
        if status is not None:
            payload["status"] = status
        if tags is not None:
            payload["tags"] = list(tags)
        if author_name is not None:
            payload["author_name"] = author_name
        if image_url is not None:
            payload["image_url"] = image_url
        return RemoteArticle.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/blogs/{blog_id}/articles", payload))
        )

    def update_article(
        self,
        account_id: str,
        blog_id: str,
        article_id: str,
        *,
        title: str | None = None,
        body: str | None = None,
        excerpt: str | None = None,
        status: str | None = None,
        tags: Sequence[str] | None = None,
        author_name: str | None = None,
        image_url: str | None = None,
    ) -> RemoteArticle:
        """Change the live article in place. Needs the ``publish`` scope.

        Only the fields passed here are touched, and the article is addressed by
        its own id, so an edit never creates a second post on the site. At least
        one field is required.
        """
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if excerpt is not None:
            payload["excerpt"] = excerpt
        if status is not None:
            payload["status"] = status
        if tags is not None:
            payload["tags"] = list(tags)
        if author_name is not None:
            payload["author_name"] = author_name
        if image_url is not None:
            payload["image_url"] = image_url
        return RemoteArticle.model_validate(
            unwrap(
                self._http.request(
                    "PATCH",
                    f"/accounts/{account_id}/blogs/{blog_id}/articles/{article_id}",
                    json=payload,
                )
            )
        )

    def delete_article(self, account_id: str, blog_id: str, article_id: str) -> None:
        """Remove the article from the site. Needs ``publish``; cannot be undone."""
        self._http.delete(f"/accounts/{account_id}/blogs/{blog_id}/articles/{article_id}")

    def list_products(
        self,
        account_id: str,
        *,
        limit: int | None = None,
        status: str | None = None,
        q: str | None = None,
    ) -> builtins.list[RemoteProduct]:
        """The store's products. ``status`` is ``active``, ``draft`` or ``archived``."""
        return parse_list(
            RemoteProduct,
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/products",
                    {"limit": limit, "status": status, "q": q},
                )
            ),
        )

    def update_product(
        self,
        account_id: str,
        product_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        tags: Sequence[str] | None = None,
        product_type: str | None = None,
        vendor: str | None = None,
    ) -> RemoteProduct:
        """Change a product on the store. Needs the ``publish`` scope.

        Only the fields passed here change; at least one is required.
        """
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status
        if tags is not None:
            payload["tags"] = list(tags)
        if product_type is not None:
            payload["product_type"] = product_type
        if vendor is not None:
            payload["vendor"] = vendor
        return RemoteProduct.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}/products/{product_id}", json=payload
                )
            )
        )
