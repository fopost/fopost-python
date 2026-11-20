"""``client.designs`` — designs, their versions, exports and bulk variants."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    Design,
    DesignDeleteResult,
    DesignExport,
    DesignPost,
    DesignSaveResult,
    DesignVersion,
    TextToSlidesResult,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["DesignsResource"]


def _save_result(body: Any) -> DesignSaveResult:
    raw = body if isinstance(body, dict) else {}
    return DesignSaveResult.model_validate(
        {"design": raw.get("data"), "version": raw.get("version")}
    )


class DesignsResource(Resource):
    def list(
        self,
        *,
        workspace_id: str,
        kind: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[Design]:
        """Designs in a workspace, without their documents."""
        body = self._http.get(
            "/designs",
            {"workspace_id": workspace_id, "kind": kind, "limit": limit, "offset": offset},
        )
        return parse_list(Design, unwrap(body))

    def create(
        self,
        *,
        workspace_id: str,
        kind: str,
        name: str | None = None,
        document: Mapping[str, Any] | None = None,
        brand_voice_id: str | None = None,
    ) -> Design:
        body: dict[str, Any] = {"workspace_id": workspace_id, "kind": kind}
        optional = {
            "name": name,
            "document": dict(document) if document is not None else None,
            "brand_voice_id": brand_voice_id,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return Design.model_validate(unwrap(self._http.post("/designs", body)))

    def get(self, design_id: str) -> Design:
        return Design.model_validate(unwrap(self._http.get(f"/designs/{design_id}")))

    def update(
        self,
        design_id: str,
        *,
        name: str | Any = UNSET,
        kind: str | Any = UNSET,
        document: Mapping[str, Any] | Any = UNSET,
        create_version: bool | Any = UNSET,
    ) -> DesignSaveResult:
        """Partial update. ``create_version=True`` also saves a version of the document."""
        body = drop_unset(
            {
                "name": name,
                "kind": kind,
                "document": dict(document) if document is not UNSET else UNSET,
                "create_version": create_version,
            }
        )
        return _save_result(self._http.patch(f"/designs/{design_id}", body))

    def delete(self, design_id: str) -> DesignDeleteResult:
        return DesignDeleteResult.model_validate(unwrap(self._http.delete(f"/designs/{design_id}")))

    def versions(
        self, design_id: str, *, include_document: bool = False
    ) -> builtins.list[DesignVersion]:
        """Saved versions, newest first. Documents are left out unless asked for."""
        body = self._http.get(
            f"/designs/{design_id}/versions",
            {"include": "document" if include_document else None},
        )
        return parse_list(DesignVersion, unwrap(body))

    def restore_version(self, design_id: str, version_id: str) -> DesignSaveResult:
        return _save_result(self._http.post(f"/designs/{design_id}/versions/{version_id}/restore"))

    def duplicate(self, design_id: str, *, name: str | None = None) -> Design:
        body = {"name": name} if name is not None else {}
        return Design.model_validate(
            unwrap(self._http.post(f"/designs/{design_id}/duplicate", body))
        )

    def export(
        self,
        design_id: str,
        *,
        format: str,
        page_indexes: Sequence[int] | None = None,
        duration_sec: int | None = None,
    ) -> DesignExport:
        """Render to ``png``, ``jpg``, ``pdf``, ``mp4`` or ``gif``; files land in the library."""
        body: dict[str, Any] = {"format": format}
        if page_indexes is not None:
            body["page_indexes"] = builtins.list(page_indexes)
        if duration_sec is not None:
            body["duration_sec"] = duration_sec
        return DesignExport.model_validate(
            unwrap(self._http.post(f"/designs/{design_id}/export", body))
        )

    def bulk_create(
        self,
        design_id: str,
        *,
        rows: Sequence[Mapping[str, Any]],
        name_column: str | None = None,
    ) -> builtins.list[Design]:
        """One new design per row, filling the template's fields from the row's columns."""
        body: dict[str, Any] = {"rows": [dict(row) for row in rows]}
        if name_column is not None:
            body["name_column"] = name_column
        return parse_list(Design, unwrap(self._http.post(f"/designs/{design_id}/bulk", body)))

    def posts(self, design_id: str) -> builtins.list[DesignPost]:
        """Posts that use this design's exports."""
        return parse_list(DesignPost, unwrap(self._http.get(f"/designs/{design_id}/posts")))

    def text_to_slides(
        self,
        *,
        workspace_id: str,
        text: str | None = None,
        post_id: str | None = None,
        max_slides: int | None = None,
        brand_voice_id: str | None = None,
    ) -> TextToSlidesResult:
        """Draft carousel slide copy from ``text`` or a post. Uses AI credits."""
        body: dict[str, Any] = {"workspace_id": workspace_id}
        optional = {
            "text": text,
            "post_id": post_id,
            "max_slides": max_slides,
            "brand_voice_id": brand_voice_id,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return TextToSlidesResult.model_validate(
            unwrap(self._http.post("/designs/text-to-slides", body))
        )

    def from_post(
        self,
        *,
        workspace_id: str,
        text: str | None = None,
        post_id: str | None = None,
        style: str | None = None,
        preset: str | None = None,
        account_id: str | None = None,
        carousel: bool | None = None,
        name: str | None = None,
        brand_voice_id: str | None = None,
    ) -> Design:
        """Create a design from ``text`` or a post's text."""
        body: dict[str, Any] = {"workspace_id": workspace_id}
        optional = {
            "text": text,
            "post_id": post_id,
            "style": style,
            "preset": preset,
            "account_id": account_id,
            "carousel": carousel,
            "name": name,
            "brand_voice_id": brand_voice_id,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return Design.model_validate(unwrap(self._http.post("/designs/from-post", body)))
