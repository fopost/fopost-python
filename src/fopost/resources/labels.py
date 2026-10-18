"""``client.labels`` — workspace labels you can attach to posts."""

from __future__ import annotations

from .._http import unwrap
from ..models import Label
from ._base import Resource, parse_list

__all__ = ["LabelsResource"]


class LabelsResource(Resource):
    def list(self, *, workspace_id: str | None = None) -> list[Label]:
        return parse_list(Label, unwrap(self._http.get("/labels", {"workspace_id": workspace_id})))

    def create(self, *, workspace_id: str, name: str, color: str) -> Label:
        body = {"workspace_id": workspace_id, "name": name, "color": color}
        return Label.model_validate(unwrap(self._http.post("/labels", body)))

    def get(self, label_id: str) -> Label:
        return Label.model_validate(unwrap(self._http.get(f"/labels/{label_id}")))

    def update(self, label_id: str, *, name: str, color: str) -> Label:
        """Both fields are required by the API, so this is a full replace."""
        return Label.model_validate(
            unwrap(self._http.put(f"/labels/{label_id}", {"name": name, "color": color}))
        )

    def delete(self, label_id: str) -> None:
        self._http.delete(f"/labels/{label_id}")
