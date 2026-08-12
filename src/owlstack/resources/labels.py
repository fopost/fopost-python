"""``client.labels`` — workspace labels you can attach to posts."""

from __future__ import annotations

from .._http import unwrap
from ..models import Label
from ._base import Resource, parse_list

__all__ = ["LabelsResource"]


class LabelsResource(Resource):
    def list(self, *, workspace_id: str | None = None) -> list[Label]:
        return parse_list(Label, unwrap(self._http.get("/labels", {"workspace_id": workspace_id})))
