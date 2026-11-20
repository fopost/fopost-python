"""``client.fonts`` — the built-in font library and a workspace's uploaded fonts."""

from __future__ import annotations

from typing import Any

from .._http import unwrap
from ..models import FontList, UploadedFont
from ._base import Resource
from .posts import FileInput, _read_file

__all__ = ["FontsResource"]


class FontsResource(Resource):
    def list(self, *, workspace_id: str | None = None) -> FontList:
        """The built-in library, plus the workspace's uploads when ``workspace_id`` is set."""
        return FontList.model_validate(
            unwrap(self._http.get("/fonts", {"workspace_id": workspace_id}))
        )

    def upload(
        self,
        *,
        workspace_id: str,
        file: FileInput,
        family: str | None = None,
        weight: int | None = None,
        style: str | None = None,
    ) -> UploadedFont:
        """Upload a font file: a path, an open binary file, or ``(filename, bytes, mime)``."""
        fields: dict[str, Any] = {"workspace_id": workspace_id}
        if family is not None:
            fields["family"] = family
        if weight is not None:
            fields["weight"] = str(weight)
        if style is not None:
            fields["style"] = style
        body = self._http.send_multipart(
            "POST", "/fonts", fields=fields, files=[("file", _read_file(file))]
        )
        return UploadedFont.model_validate(unwrap(body))

    def delete(self, font_id: str) -> None:
        self._http.delete(f"/fonts/{font_id}")
