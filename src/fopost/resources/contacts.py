"""``client.contacts`` — the people behind the inbox, and the fields kept about them.

A contact is one human however many handles they write from. An inbound inbox
item files its author, a reply files whoever you answered, and both fold into
whatever is already on file, so the same person never becomes two rows.
"""

from __future__ import annotations

import builtins
from typing import Any

from .._http import unwrap
from ..models import (
    Contact,
    ContactChannel,
    ContactConversation,
    ContactField,
    ContactImportResult,
    ConversationAnalytics,
    Page,
    PageMeta,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["ContactsResource"]


def _channels(channels: list[ContactChannel] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        c.model_dump(exclude_none=True) if isinstance(c, ContactChannel) else c for c in channels
    ]


class ContactsResource(Resource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        search: str | None = None,
        platform: str | None = None,
        source: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[Contact]:
        """One page of contacts, most recently active first.

        Omit ``workspace_id`` to span every workspace the key can reach; each
        contact then carries ``workspace_id``.
        """
        body = self._http.get(
            "/contacts",
            {
                "workspace_id": workspace_id,
                "search": search,
                "platform": platform,
                "source": source,
                "page": page,
                "per_page": per_page,
            },
        )
        items = parse_list(Contact, body.get("data") if isinstance(body, dict) else body)
        raw = body.get("pagination") if isinstance(body, dict) else None
        meta = PageMeta.model_validate(raw) if isinstance(raw, dict) else PageMeta()
        return Page[Contact](items=items, meta=meta)

    def get(self, contact_id: str) -> Contact:
        return Contact.model_validate(unwrap(self._http.get(f"/contacts/{contact_id}")))

    def create(
        self,
        *,
        workspace_id: str,
        channels: builtins.list[ContactChannel] | builtins.list[dict[str, Any]],
        display_name: str | None = None,
        note: str | None = None,
        fields: dict[str, str] | None = None,
    ) -> Contact:
        """Create a contact.

        Folds into the contact that already holds the first channel, so this
        cannot duplicate someone the inbox has already met.
        """
        body: dict[str, Any] = {
            "workspace_id": workspace_id,
            "channels": _channels(channels),
        }
        if display_name is not None:
            body["display_name"] = display_name
        if note is not None:
            body["note"] = note
        if fields is not None:
            body["fields"] = fields
        return Contact.model_validate(unwrap(self._http.post("/contacts", json=body)))

    def update(
        self,
        contact_id: str,
        *,
        display_name: str | None | Any = UNSET,
        channels: builtins.list[ContactChannel] | builtins.list[dict[str, Any]] | Any = UNSET,
        note: str | None | Any = UNSET,
        fields: dict[str, str | None] | Any = UNSET,
    ) -> Contact:
        """Patch a contact. A field set to ``None`` or ``""`` is cleared."""
        body = drop_unset(
            {
                "display_name": display_name,
                "channels": _channels(channels) if channels is not UNSET else UNSET,
                "note": note,
                "fields": fields,
            }
        )
        return Contact.model_validate(
            unwrap(self._http.request("PATCH", f"/contacts/{contact_id}", json=body))
        )

    def delete(self, contact_id: str) -> bool:
        """Remove a contact. Their messages stay in the inbox and file them again."""
        body = unwrap(self._http.delete(f"/contacts/{contact_id}"))
        return bool(body.get("deleted", True)) if isinstance(body, dict) else True

    def conversations(
        self, contact_id: str, *, limit: int | None = None
    ) -> builtins.list[ContactConversation]:
        """The threads this person appears in, newest first."""
        return parse_list(
            ContactConversation,
            unwrap(self._http.get(f"/contacts/{contact_id}/conversations", {"limit": limit})),
        )

    def import_csv(self, *, workspace_id: str, csv: str) -> ContactImportResult:
        """Import from CSV text.

        ``platform`` and ``handle`` are required columns. Any other column is
        read as a custom field key, and one matching no field is reported back
        in ``unknown_columns`` rather than stored.
        """
        return ContactImportResult.model_validate(
            unwrap(
                self._http.post("/contacts/import", json={"workspace_id": workspace_id, "csv": csv})
            )
        )

    # ─── Custom fields ─────────────────────────────────────────────

    def list_fields(self, *, workspace_id: str) -> builtins.list[ContactField]:
        """The columns this workspace keeps about its contacts, in display order."""
        return parse_list(
            ContactField, unwrap(self._http.get("/contacts/fields", {"workspace_id": workspace_id}))
        )

    def create_field(
        self,
        *,
        workspace_id: str,
        key: str,
        name: str,
        type: str = "text",
        options: builtins.list[str] | None = None,
    ) -> ContactField:
        return ContactField.model_validate(
            unwrap(
                self._http.request(
                    "POST",
                    "/contacts/fields",
                    params={"workspace_id": workspace_id},
                    json={
                        "key": key,
                        "name": name,
                        "type": type,
                        "options": options or [],
                    },
                )
            )
        )

    def update_field(
        self,
        field_id: str,
        *,
        name: str | Any = UNSET,
        options: builtins.list[str] | Any = UNSET,
        position: int | Any = UNSET,
    ) -> ContactField:
        """The key and the type are fixed once created; the name and options are not."""
        body = drop_unset({"name": name, "options": options, "position": position})
        return ContactField.model_validate(
            unwrap(self._http.request("PATCH", f"/contacts/fields/{field_id}", json=body))
        )

    def delete_field(self, field_id: str) -> bool:
        """Remove the field and every answer to it."""
        body = unwrap(self._http.delete(f"/contacts/fields/{field_id}"))
        return bool(body.get("deleted", True)) if isinstance(body, dict) else True

    # ─── Per-conversation analytics ────────────────────────────────

    def conversation_analytics(
        self,
        *,
        workspace_id: str | None = None,
        account_id: str | None = None,
        days: int | None = None,
        sort: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> ConversationAnalytics:
        """Volume and median reply time per thread.

        Needs the ``analytics`` scope rather than ``inbox``.
        """
        return ConversationAnalytics.model_validate(
            unwrap(
                self._http.get(
                    "/analytics/inbox/conversations",
                    {
                        "workspace_id": workspace_id,
                        "accountId": account_id,
                        "days": days,
                        "sort": sort,
                        "page": page,
                        "per_page": per_page,
                    },
                )
            )
        )
