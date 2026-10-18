"""``client.connect_sessions`` — hosted connect links for your end users."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import ConnectSession
from ._base import Resource

__all__ = ["ConnectSessionsResource"]


class ConnectSessionsResource(Resource):
    def create(
        self,
        *,
        external_user_id: str,
        platforms: Sequence[str],
        workspace_id: str | None = None,
        redirect_url: str | None = None,
        branding: Mapping[str, str] | None = None,
    ) -> ConnectSession:
        """Mint a single-use link, open for one hour, that connects an account.

        ``redirect_url`` must be on a domain in the workspace redirect allowlist.
        ``branding`` takes ``name`` and ``logo_url``. ``workspace_id`` may be
        omitted for a key bound to one workspace.
        """
        body: dict[str, Any] = {
            "externalUserId": external_user_id,
            "platforms": list(platforms),
        }
        if workspace_id is not None:
            body["workspaceId"] = workspace_id
        if redirect_url is not None:
            body["redirectUrl"] = redirect_url
        if branding is not None:
            body["branding"] = {
                "name": branding.get("name"),
                "logoUrl": branding.get("logo_url", branding.get("logoUrl")),
            }
            body["branding"] = {k: v for k, v in body["branding"].items() if v is not None}
        return ConnectSession.model_validate(unwrap(self._http.post("/connect-sessions", body)))

    def get(self, session_id: str) -> ConnectSession:
        """Poll the outcome: ``status`` moves to ``used`` once ``account_id`` is set."""
        return ConnectSession.model_validate(
            unwrap(self._http.get(f"/connect-sessions/{session_id}"))
        )
