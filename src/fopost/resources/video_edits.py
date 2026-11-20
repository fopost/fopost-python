"""``client.video_edits`` — run a library video through a chain of edit operations."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import VideoEdit, VideoEditOperation, VideoEditOpInfo
from ._base import Resource, parse_list

__all__ = ["VideoEditsResource"]

OperationInput = Mapping[str, Any] | VideoEditOperation


def _operation(op: OperationInput) -> dict[str, Any]:
    if isinstance(op, VideoEditOperation):
        return {"op": op.op, "params": dict(op.params)}
    out: dict[str, Any] = {"op": op["op"]}
    if op.get("params") is not None:
        out["params"] = dict(op["params"])
    return out


class VideoEditsResource(Resource):
    def ops(self) -> builtins.list[VideoEditOpInfo]:
        """Every operation, whether it is available here, and whether it uses AI credits."""
        return parse_list(VideoEditOpInfo, unwrap(self._http.get("/video-edits/ops")))

    def list(
        self,
        *,
        workspace_id: str | None = None,
        media_id: str | None = None,
        limit: int | None = None,
    ) -> builtins.list[VideoEdit]:
        body = self._http.get(
            "/video-edits",
            {"workspace_id": workspace_id, "media_id": media_id, "limit": limit},
        )
        return parse_list(VideoEdit, unwrap(body))

    def create(
        self,
        *,
        media_id: str,
        operations: Sequence[OperationInput],
        workspace_id: str | None = None,
    ) -> VideoEdit:
        """Queue an edit. ``operations`` are ``{"op": ..., "params": {...}}`` applied in order."""
        body: dict[str, Any] = {
            "media_id": media_id,
            "operations": [_operation(op) for op in operations],
        }
        if workspace_id is not None:
            body["workspace_id"] = workspace_id
        return VideoEdit.model_validate(unwrap(self._http.post("/video-edits", body)))

    def get(self, edit_id: str, *, workspace_id: str | None = None) -> VideoEdit:
        return VideoEdit.model_validate(
            unwrap(self._http.get(f"/video-edits/{edit_id}", {"workspace_id": workspace_id}))
        )
