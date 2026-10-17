"""``client.whatsapp`` — a WhatsApp Business connection.

The platform owns templates, flows, the business profile and the commerce
settings, so every method here is a live read or write against the customer's
own WhatsApp Business Account. Nothing is cached, and all of it answers 503
until WhatsApp is set up on the deployment.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    WhatsappBlockResult,
    WhatsappCommerceSettings,
    WhatsappEncryptionKeyStatus,
    WhatsappFlow,
    WhatsappFlowJsonResult,
    WhatsappFlowResponse,
    WhatsappGroup,
    WhatsappProfile,
    WhatsappSandboxSession,
    WhatsappTemplate,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["WhatsappResource"]


class WhatsappResource(Resource):
    # ─── Profile ──────────────────────────────────────────────────

    def get_profile(self, account_id: str) -> WhatsappProfile:
        return WhatsappProfile.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/profile"))
        )

    def update_profile(
        self,
        account_id: str,
        *,
        about: str | None | Any = UNSET,
        address: str | None | Any = UNSET,
        description: str | None | Any = UNSET,
        vertical: str | None | Any = UNSET,
        websites: Sequence[str] | None | Any = UNSET,
        profile_picture_media_id: str | None | Any = UNSET,
    ) -> WhatsappProfile:
        body = drop_unset(
            {
                "about": about,
                "address": address,
                "description": description,
                "vertical": vertical,
                "websites": list(websites) if isinstance(websites, Sequence) else websites,
                "profile_picture_media_id": profile_picture_media_id,
            }
        )
        return WhatsappProfile.model_validate(
            unwrap(
                self._http.request("PATCH", f"/accounts/{account_id}/whatsapp/profile", json=body)
            )
        )

    def request_display_name(self, account_id: str, display_name: str) -> dict[str, Any]:
        """A review, not a write: the number keeps its old name until it passes."""
        body = unwrap(
            self._http.post(
                f"/accounts/{account_id}/whatsapp/profile/display-name",
                {"display_name": display_name},
            )
        )
        return body if isinstance(body, dict) else {}

    def set_username(self, account_id: str, username: str) -> WhatsappProfile:
        return WhatsappProfile.model_validate(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/whatsapp/profile/username", {"username": username}
                )
            )
        )

    # ─── Templates ────────────────────────────────────────────────

    def list_templates(
        self, account_id: str, *, after: str | None = None
    ) -> list[WhatsappTemplate]:
        return parse_list(
            WhatsappTemplate,
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/templates", {"after": after})),
        )

    def list_template_library(
        self, account_id: str, *, search: str | None = None
    ) -> list[dict[str, Any]]:
        """The platform's pre-written templates, for adapting instead of drafting."""
        body = unwrap(
            self._http.get(f"/accounts/{account_id}/whatsapp/templates/library", {"search": search})
        )
        return list(body) if isinstance(body, list) else []

    def get_template(self, account_id: str, template_id: str) -> WhatsappTemplate:
        return WhatsappTemplate.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/templates/{template_id}"))
        )

    def create_template(
        self,
        account_id: str,
        *,
        name: str,
        language: str,
        category: str,
        components: Sequence[Mapping[str, Any]],
        allow_category_change: bool | None | Any = UNSET,
    ) -> WhatsappTemplate:
        """Files a template for review; the result carries the status it was given."""
        body = drop_unset(
            {
                "name": name,
                "language": language,
                "category": category,
                "components": [dict(c) for c in components],
                "allow_category_change": allow_category_change,
            }
        )
        return WhatsappTemplate.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/whatsapp/templates", body))
        )

    def import_template(
        self,
        account_id: str,
        *,
        library_template_name: str,
        name: str,
        language: str,
        category: str,
        library_template_button_inputs: Sequence[Mapping[str, Any]] | None | Any = UNSET,
    ) -> WhatsappTemplate:
        inputs = (
            [dict(i) for i in library_template_button_inputs]
            if isinstance(library_template_button_inputs, Sequence)
            else library_template_button_inputs
        )
        body = drop_unset(
            {
                "library_template_name": library_template_name,
                "name": name,
                "language": language,
                "category": category,
                "library_template_button_inputs": inputs,
            }
        )
        return WhatsappTemplate.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/whatsapp/templates/import", body))
        )

    def update_template(
        self,
        account_id: str,
        template_id: str,
        *,
        category: str | None | Any = UNSET,
        components: Sequence[Mapping[str, Any]] | None | Any = UNSET,
    ) -> WhatsappTemplate:
        mapped = [dict(c) for c in components] if isinstance(components, Sequence) else components
        body = drop_unset({"category": category, "components": mapped})
        return WhatsappTemplate.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}/whatsapp/templates/{template_id}", json=body
                )
            )
        )

    def delete_template(self, account_id: str, template_id: str, *, name: str) -> None:
        """The name is required: it is what the platform deletes by."""
        from urllib.parse import quote

        self._http.delete(
            f"/accounts/{account_id}/whatsapp/templates/{template_id}?name={quote(name)}"
        )

    # ─── Groups ───────────────────────────────────────────────────

    def list_groups(self, account_id: str) -> list[WhatsappGroup]:
        return parse_list(
            WhatsappGroup, unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/groups"))
        )

    def create_group(
        self, account_id: str, *, subject: str, description: str | None | Any = UNSET
    ) -> WhatsappGroup:
        """Participation is invite-only: send the invite link, there is no add."""
        body = drop_unset({"subject": subject, "description": description})
        return WhatsappGroup.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/whatsapp/groups", body))
        )

    def get_group(self, account_id: str, group_id: str) -> WhatsappGroup:
        return WhatsappGroup.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/groups/{group_id}"))
        )

    def update_group(
        self,
        account_id: str,
        group_id: str,
        *,
        subject: str | None | Any = UNSET,
        description: str | None | Any = UNSET,
    ) -> WhatsappGroup:
        body = drop_unset({"subject": subject, "description": description})
        return WhatsappGroup.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}/whatsapp/groups/{group_id}", json=body
                )
            )
        )

    def delete_group(self, account_id: str, group_id: str) -> None:
        self._http.delete(f"/accounts/{account_id}/whatsapp/groups/{group_id}")

    def get_group_invite_link(self, account_id: str, group_id: str) -> str | None:
        body = unwrap(
            self._http.get(f"/accounts/{account_id}/whatsapp/groups/{group_id}/invite-link")
        )
        return body.get("inviteLink") if isinstance(body, dict) else None

    def reset_group_invite_link(self, account_id: str, group_id: str) -> str | None:
        """Issues a new link and invalidates the old one."""
        body = unwrap(
            self._http.post(f"/accounts/{account_id}/whatsapp/groups/{group_id}/invite-link")
        )
        return body.get("inviteLink") if isinstance(body, dict) else None

    def remove_group_participants(
        self, account_id: str, group_id: str, users: Sequence[str]
    ) -> None:
        self._http.delete(
            f"/accounts/{account_id}/whatsapp/groups/{group_id}/participants",
            json={"users": list(users)},
        )

    # ─── Blocking ─────────────────────────────────────────────────

    def list_blocked(self, account_id: str, *, after: str | None = None) -> list[str]:
        body = unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/block", {"after": after}))
        return [str(u) for u in body] if isinstance(body, list) else []

    def block_users(self, account_id: str, users: Sequence[str]) -> WhatsappBlockResult:
        return WhatsappBlockResult.model_validate(
            unwrap(
                self._http.post(f"/accounts/{account_id}/whatsapp/block", {"users": list(users)})
            )
        )

    def unblock_users(self, account_id: str, users: Sequence[str]) -> WhatsappBlockResult:
        return WhatsappBlockResult.model_validate(
            unwrap(
                self._http.delete(
                    f"/accounts/{account_id}/whatsapp/block", json={"users": list(users)}
                )
            )
        )

    # ─── Commerce ─────────────────────────────────────────────────

    def get_commerce_settings(self, account_id: str) -> WhatsappCommerceSettings:
        return WhatsappCommerceSettings.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/commerce"))
        )

    def update_commerce_settings(
        self,
        account_id: str,
        *,
        cart_enabled: bool | None | Any = UNSET,
        catalog_visible: bool | None | Any = UNSET,
    ) -> WhatsappCommerceSettings:
        body = drop_unset({"is_cart_enabled": cart_enabled, "is_catalog_visible": catalog_visible})
        return WhatsappCommerceSettings.model_validate(
            unwrap(
                self._http.request("PATCH", f"/accounts/{account_id}/whatsapp/commerce", json=body)
            )
        )

    def link_catalog(self, account_id: str, catalog_id: str) -> WhatsappCommerceSettings:
        return WhatsappCommerceSettings.model_validate(
            unwrap(
                self._http.post(
                    f"/accounts/{account_id}/whatsapp/commerce/catalog",
                    {"catalog_id": catalog_id},
                )
            )
        )

    # ─── Flows ────────────────────────────────────────────────────

    def list_flows(self, account_id: str) -> list[WhatsappFlow]:
        return parse_list(
            WhatsappFlow, unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/flows"))
        )

    def get_flow(self, account_id: str, flow_id: str) -> WhatsappFlow:
        return WhatsappFlow.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/flows/{flow_id}"))
        )

    def create_flow(
        self,
        account_id: str,
        *,
        name: str,
        categories: Sequence[str],
        endpoint_uri: str | None | Any = UNSET,
        clone_flow_id: str | None | Any = UNSET,
    ) -> WhatsappFlow:
        body = drop_unset(
            {
                "name": name,
                "categories": list(categories),
                "endpoint_uri": endpoint_uri,
                "clone_flow_id": clone_flow_id,
            }
        )
        return WhatsappFlow.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/whatsapp/flows", body))
        )

    def update_flow(
        self,
        account_id: str,
        flow_id: str,
        *,
        name: str | None | Any = UNSET,
        categories: Sequence[str] | None | Any = UNSET,
        endpoint_uri: str | None | Any = UNSET,
    ) -> WhatsappFlow:
        mapped = list(categories) if isinstance(categories, Sequence) else categories
        body = drop_unset({"name": name, "categories": mapped, "endpoint_uri": endpoint_uri})
        return WhatsappFlow.model_validate(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}/whatsapp/flows/{flow_id}", json=body
                )
            )
        )

    def delete_flow(self, account_id: str, flow_id: str) -> None:
        """Drafts only; a published flow is deprecated instead."""
        self._http.delete(f"/accounts/{account_id}/whatsapp/flows/{flow_id}")

    def upload_flow_json(
        self, account_id: str, flow_id: str, flow_json: Mapping[str, Any]
    ) -> WhatsappFlowJsonResult:
        """The platform answers with its validation errors rather than refusing."""
        return WhatsappFlowJsonResult.model_validate(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/whatsapp/flows/{flow_id}/json",
                    {"flow_json": dict(flow_json)},
                )
            )
        )

    def publish_flow(self, account_id: str, flow_id: str) -> WhatsappFlow:
        return WhatsappFlow.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/whatsapp/flows/{flow_id}/publish"))
        )

    def deprecate_flow(self, account_id: str, flow_id: str) -> WhatsappFlow:
        return WhatsappFlow.model_validate(
            unwrap(self._http.post(f"/accounts/{account_id}/whatsapp/flows/{flow_id}/deprecate"))
        )

    def list_flow_responses(self, account_id: str) -> list[WhatsappFlowResponse]:
        return parse_list(
            WhatsappFlowResponse,
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/flows/responses")),
        )

    def get_encryption_key_status(self, account_id: str) -> WhatsappEncryptionKeyStatus:
        return WhatsappEncryptionKeyStatus.model_validate(
            unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/flows/encryption-key"))
        )

    def set_encryption_key(
        self, account_id: str, business_public_key: str
    ) -> WhatsappEncryptionKeyStatus:
        """The public half only; the private half stays with the customer."""
        return WhatsappEncryptionKeyStatus.model_validate(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/whatsapp/flows/encryption-key",
                    {"business_public_key": business_public_key},
                )
            )
        )

    # ─── Account state and sandbox ────────────────────────────────

    def get_account_events(self, account_id: str) -> dict[str, Any]:
        body = unwrap(self._http.get(f"/accounts/{account_id}/whatsapp/events"))
        return body if isinstance(body, dict) else {}

    def list_sandbox_sessions(self, *, workspace_id: str) -> list[WhatsappSandboxSession]:
        return parse_list(
            WhatsappSandboxSession,
            unwrap(self._http.get("/whatsapp/sandbox/sessions", {"workspaceId": workspace_id})),
        )

    def create_sandbox_session(
        self, *, workspace_id: str, phone_number: str
    ) -> WhatsappSandboxSession:
        """Sends a template from the platform-owned test number; needs the publish scope."""
        return WhatsappSandboxSession.model_validate(
            unwrap(
                self._http.post(
                    "/whatsapp/sandbox/sessions",
                    {"workspaceId": workspace_id, "phoneNumber": phone_number},
                )
            )
        )
