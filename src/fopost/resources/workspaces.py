"""``client.workspaces`` — the workspaces the key can reach."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._http import unwrap
from ..models import Workspace
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["WorkspacesResource"]


class WorkspacesResource(Resource):
    def list(self) -> list[Workspace]:
        return parse_list(Workspace, unwrap(self._http.get("/workspaces")))

    def get(self, workspace_id: str) -> Workspace:
        return Workspace.model_validate(unwrap(self._http.get(f"/workspaces/{workspace_id}")))

    def create(
        self,
        *,
        name: str,
        type: str | None = None,
        logo: str | None = None,
        website: str | None = None,
        timezone: str | None = None,
        country: str | None = None,
        description: str | None = None,
        language: str | None = None,
    ) -> Workspace:
        body: dict[str, Any] = {"name": name}
        optional = {
            "type": type,
            "logo": logo,
            "website": website,
            "timezone": timezone,
            "country": country,
            "description": description,
            "language": language,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return Workspace.model_validate(unwrap(self._http.post("/workspaces", body)))

    def update(
        self,
        workspace_id: str,
        *,
        name: str | Any = UNSET,
        type: str | Any = UNSET,
        logo: str | None | Any = UNSET,
        website: str | None | Any = UNSET,
        timezone: str | Any = UNSET,
        country: str | None | Any = UNSET,
        description: str | None | Any = UNSET,
        language: str | Any = UNSET,
        require_approval: bool | Any = UNSET,
        ai_alt_text_enabled: bool | Any = UNSET,
        brand_color: str | None | Any = UNSET,
        connect_redirect_domains: Sequence[str] | Any = UNSET,
    ) -> Workspace:
        """Partial update; needs the owner or admin role."""
        body = drop_unset(
            {
                "name": name,
                "type": type,
                "logo": logo,
                "website": website,
                "timezone": timezone,
                "country": country,
                "description": description,
                "language": language,
                "requireApproval": require_approval,
                "aiAltTextEnabled": ai_alt_text_enabled,
                "brandColor": brand_color,
                "connectRedirectDomains": (
                    list(connect_redirect_domains)
                    if connect_redirect_domains is not UNSET
                    else UNSET
                ),
            }
        )
        return Workspace.model_validate(unwrap(self._http.put(f"/workspaces/{workspace_id}", body)))

    def delete(self, workspace_id: str) -> None:
        """Soft-delete. 409 while accounts are still connected or it is your only workspace."""
        self._http.delete(f"/workspaces/{workspace_id}")
