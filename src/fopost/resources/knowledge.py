"""``client.knowledge`` — what the workspace has told FoPost about itself.

A source is an FAQ, a note, a page on your own site or a plain-text/CSV item
from the media library. Retrieval over these is what grounds a drafted inbox
reply in your own answers instead of an invented one.
"""

from __future__ import annotations

import builtins

from .._http import unwrap
from ..models import KnowledgeMatch, KnowledgeSource, KnowledgeSyncResult
from ._base import Resource, parse_list

__all__ = ["KnowledgeResource"]


class KnowledgeResource(Resource):
    def list(self, *, workspace_id: str | None = None) -> builtins.list[KnowledgeSource]:
        """Every source in the workspace. Only a ``ready`` one is searched."""
        body = self._http.get("/knowledge/sources", {"workspace_id": workspace_id})
        return parse_list(KnowledgeSource, unwrap(body))

    def create(
        self,
        *,
        kind: str,
        title: str,
        content: str | None = None,
        url: str | None = None,
        media_id: str | None = None,
        brand_voice_id: str | None = None,
        workspace_id: str | None = None,
    ) -> KnowledgeSource:
        """Add a source and queue it for indexing, so it comes back ``pending``.

        ``kind`` is ``faq``, ``text``, ``url`` or ``file``. An ``faq`` or ``text``
        source needs ``content``, a ``url`` source needs ``url``, and a ``file``
        source needs ``media_id`` pointing at a plain-text or CSV media item in
        the same workspace.
        """
        body = self._http.post(
            "/knowledge/sources",
            {
                "kind": kind,
                "title": title,
                "content": content,
                "url": url,
                "media_id": media_id,
                "brand_voice_id": brand_voice_id,
                "workspace_id": workspace_id,
            },
        )
        return KnowledgeSource.model_validate(unwrap(body))

    def update(
        self,
        source_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        url: str | None = None,
        brand_voice_id: str | None = None,
    ) -> KnowledgeSource:
        """Changing ``content`` or ``url`` returns the source to ``pending``."""
        body = self._http.patch(
            f"/knowledge/sources/{source_id}",
            {
                "title": title,
                "content": content,
                "url": url,
                "brand_voice_id": brand_voice_id,
            },
        )
        return KnowledgeSource.model_validate(unwrap(body))

    def delete(self, source_id: str) -> None:
        """Remove the source and every passage indexed from it."""
        self._http.delete(f"/knowledge/sources/{source_id}")

    def sync(self, source_id: str) -> KnowledgeSyncResult:
        """Read the source again — a ``url`` source is re-fetched. Returns once queued."""
        body = self._http.post(f"/knowledge/sources/{source_id}/sync", {})
        return KnowledgeSyncResult.model_validate(unwrap(body))

    def search(
        self,
        q: str,
        *,
        top_k: int | None = None,
        brand_voice_id: str | None = None,
        workspace_id: str | None = None,
    ) -> builtins.list[KnowledgeMatch]:
        """The passages closest to a question. Empty when nothing stored answers it."""
        body = self._http.get(
            "/knowledge/search",
            {
                "q": q,
                "top_k": top_k,
                "brand_voice_id": brand_voice_id,
                "workspace_id": workspace_id,
            },
        )
        return parse_list(KnowledgeMatch, unwrap(body))
