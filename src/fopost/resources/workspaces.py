"""``client.workspaces`` — the workspaces the key can reach."""

from __future__ import annotations

from .._http import unwrap
from ..models import Workspace
from ._base import Resource, parse_list

__all__ = ["WorkspacesResource"]


class WorkspacesResource(Resource):
    def list(self) -> list[Workspace]:
        return parse_list(Workspace, unwrap(self._http.get("/workspaces")))

    def get(self, workspace_id: str) -> Workspace:
        return Workspace.model_validate(unwrap(self._http.get(f"/workspaces/{workspace_id}")))
