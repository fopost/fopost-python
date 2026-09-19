"""``client.account_groups`` — named sets of accounts to post to together."""

from __future__ import annotations

import builtins
from collections.abc import Sequence

from .._http import unwrap
from ..models import AccountGroup
from ._base import Resource, parse_list

__all__ = ["AccountGroupsResource"]


class AccountGroupsResource(Resource):
    def list(self, *, workspace_id: str | None = None) -> builtins.list[AccountGroup]:
        return parse_list(
            AccountGroup,
            unwrap(self._http.get("/account-groups", {"workspace_id": workspace_id})),
        )

    def create(
        self,
        *,
        workspace_id: str,
        name: str,
        account_ids: Sequence[str] | None = None,
    ) -> AccountGroup:
        body: dict[str, object] = {"workspace_id": workspace_id, "name": name}
        if account_ids is not None:
            body["account_ids"] = builtins.list(account_ids)
        return AccountGroup.model_validate(unwrap(self._http.post("/account-groups", body)))

    def get(self, group_id: str) -> AccountGroup:
        return AccountGroup.model_validate(unwrap(self._http.get(f"/account-groups/{group_id}")))

    def update(self, group_id: str, *, name: str) -> AccountGroup:
        """Rename the group."""
        return AccountGroup.model_validate(
            unwrap(self._http.request("PATCH", f"/account-groups/{group_id}", json={"name": name}))
        )

    def delete(self, group_id: str) -> None:
        self._http.delete(f"/account-groups/{group_id}")

    def set_members(self, group_id: str, account_ids: Sequence[str]) -> AccountGroup:
        """Replace the group's members with exactly these accounts."""
        return AccountGroup.model_validate(
            unwrap(
                self._http.put(
                    f"/account-groups/{group_id}/members",
                    {"account_ids": builtins.list(account_ids)},
                )
            )
        )
