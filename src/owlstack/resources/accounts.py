"""``client.accounts`` — the social accounts connected to a workspace."""

from __future__ import annotations

from typing import Any

from .._http import unwrap
from ..models import SocialAccount
from ._base import Resource, parse_list

__all__ = ["AccountsResource"]


class AccountsResource(Resource):
    def list(self, *, workspace_id: str | None = None) -> list[SocialAccount]:
        """Connected accounts, across every workspace unless one is named."""
        # This endpoint reads a camelCase query param; posts and labels use snake.
        return parse_list(
            SocialAccount,
            unwrap(self._http.get("/accounts", {"workspaceId": workspace_id})),
        )

    def get(self, account_id: str) -> SocialAccount:
        return SocialAccount.model_validate(unwrap(self._http.get(f"/accounts/{account_id}")))

    def health(self, account_id: str) -> dict[str, Any]:
        """Token validity and last-check detail for one account."""
        body = unwrap(self._http.get(f"/accounts/{account_id}/health"))
        return body if isinstance(body, dict) else {"data": body}
