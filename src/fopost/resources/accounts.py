"""``client.accounts`` — the social accounts connected to a workspace."""

from __future__ import annotations

from typing import Any

from .._http import unwrap
from ..models import AccountMove, AccountRename, SocialAccount
from ._base import Resource, parse_list

__all__ = ["AccountsResource"]


class AccountsResource(Resource):
    def list(
        self, *, workspace_id: str | None = None, group_id: str | None = None
    ) -> list[SocialAccount]:
        """Connected accounts, across every workspace unless one is named."""
        # This endpoint reads a camelCase workspaceId; posts and labels use snake.
        return parse_list(
            SocialAccount,
            unwrap(
                self._http.get("/accounts", {"workspaceId": workspace_id, "group_id": group_id})
            ),
        )

    def get(self, account_id: str) -> SocialAccount:
        return SocialAccount.model_validate(unwrap(self._http.get(f"/accounts/{account_id}")))

    def health(self, account_id: str) -> dict[str, Any]:
        """Token validity and last-check detail for one account."""
        body = unwrap(self._http.get(f"/accounts/{account_id}/health"))
        return body if isinstance(body, dict) else {"data": body}

    def update(self, account_id: str, *, display_name: str | None) -> AccountRename:
        """Rename the account; ``None`` or an empty string restores the platform name."""
        return AccountRename.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}", json={"display_name": display_name}
                )
            )
        )

    def move(self, account_id: str, *, workspace_id: str) -> AccountMove:
        """Move the account to another workspace the caller owns."""
        return AccountMove.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/move", {"workspace_id": workspace_id}))
        )
