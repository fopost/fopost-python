"""``client.ads`` — Meta ads, audiences and lead forms.

Every method needs the ``ads`` scope; ``boost``, ``create``, ``set_status`` and
``delete`` spend money and also need ``publish``.
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    Ad,
    AdConnection,
    AdSource,
    AudiencesResult,
    BoostablePost,
    ExternalAd,
    LeadFormSource,
    LeadsPage,
    TargetingOption,
)
from ._base import Resource, parse_list

__all__ = ["AdsResource"]


class AdsResource(Resource):
    def list(self, *, workspace_id: str | None = None) -> builtins.list[Ad]:
        """Boosts and ads created through FoPost, with insights from their last refresh."""
        return parse_list(Ad, unwrap(self._http.get("/ads", {"workspace_id": workspace_id})))

    def external(self, *, workspace_id: str | None = None) -> builtins.list[ExternalAd]:
        """Ads on the connected ad accounts that were made elsewhere. Read live, never stored."""
        return parse_list(
            ExternalAd, unwrap(self._http.get("/ads/external", {"workspace_id": workspace_id}))
        )

    def boostable(self, *, workspace_id: str | None = None) -> builtins.list[BoostablePost]:
        return parse_list(
            BoostablePost,
            unwrap(self._http.get("/ads/boostable", {"workspace_id": workspace_id})),
        )

    def connections(self, *, workspace_id: str | None = None) -> builtins.list[AdConnection]:
        return parse_list(
            AdConnection,
            unwrap(self._http.get("/ads/connections", {"workspace_id": workspace_id})),
        )

    def sources(self, *, workspace_id: str | None = None) -> builtins.list[AdSource]:
        """Each connection with the ad accounts and Pages its grant reaches."""
        return parse_list(
            AdSource, unwrap(self._http.get("/ads/sources", {"workspace_id": workspace_id}))
        )

    def authorize_meta(
        self, *, workspace_id: str, method: str | None = None, return_to: str | None = None
    ) -> str:
        """The Meta login URL; the caller finishes it in their own browser."""
        body: dict[str, Any] = {"workspaceId": workspace_id}
        if method is not None:
            body["method"] = method
        if return_to is not None:
            body["returnTo"] = return_to
        result = unwrap(self._http.post("/ads/connections/meta/authorize", body))
        url = result.get("url") if isinstance(result, dict) else None
        return str(url) if url else ""

    def delete_connection(self, connection_id: str, *, workspace_id: str) -> None:
        """Also deletes every ad record created through the connection."""
        self._http.request(
            "DELETE", f"/ads/connections/{connection_id}", params={"workspace_id": workspace_id}
        )

    def boost(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        post_id: str,
        account_id: str,
        name: str,
        goal: str,
        budget: Mapping[str, Any],
        targeting: Mapping[str, Any],
        paused: bool | None = None,
    ) -> Ad:
        """Promote a post FoPost already published. Starts paused unless ``paused=False``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "postId": post_id,
            "accountId": account_id,
            "name": name,
            "goal": goal,
            "budget": dict(budget),
            "targeting": dict(targeting),
        }
        if paused is not None:
            body["paused"] = paused
        return Ad.model_validate(unwrap(self._http.post("/ads/boost", body)))

    def create(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        page_id: str,
        name: str,
        goal: str,
        budget: Mapping[str, Any],
        targeting: Mapping[str, Any],
        text: str,
        headline: str | None = None,
        destination_url: str | None = None,
        media_url: str | None = None,
        paused: bool | None = None,
    ) -> Ad:
        """Create a standalone ad from a creative. Starts paused unless ``paused=False``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "pageId": page_id,
            "name": name,
            "goal": goal,
            "budget": dict(budget),
            "targeting": dict(targeting),
            "text": text,
        }
        optional = {
            "headline": headline,
            "destinationUrl": destination_url,
            "mediaUrl": media_url,
            "paused": paused,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return Ad.model_validate(unwrap(self._http.post("/ads", body)))

    def refresh(self, ad_id: str, *, workspace_id: str) -> Ad:
        """Read the delivery status and lifetime insights from Meta."""
        return Ad.model_validate(
            unwrap(
                self._http.request(
                    "POST", f"/ads/{ad_id}/refresh", params={"workspace_id": workspace_id}
                )
            )
        )

    def set_status(self, ad_id: str, *, workspace_id: str, status: str) -> Ad:
        """``active`` or ``paused``."""
        return Ad.model_validate(
            unwrap(
                self._http.request(
                    "PATCH",
                    f"/ads/{ad_id}",
                    json={"status": status},
                    params={"workspace_id": workspace_id},
                )
            )
        )

    def delete(self, ad_id: str, *, workspace_id: str) -> None:
        """End delivery and delete the ad on Meta as well as here."""
        self._http.request("DELETE", f"/ads/{ad_id}", params={"workspace_id": workspace_id})

    def audiences(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> AudiencesResult:
        return AudiencesResult.model_validate(
            unwrap(
                self._http.get(
                    "/ads/audiences",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "ad_account_id": ad_account_id,
                    },
                )
            )
        )

    def create_audience(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str,
        spec: Mapping[str, Any],
        description: str | None = None,
    ) -> dict[str, Any]:
        """``spec`` carries a ``subtype`` of ``CUSTOM``, ``LOOKALIKE`` or ``WEBSITE``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "name": name,
            "spec": dict(spec),
        }
        if description is not None:
            body["description"] = description
        result = unwrap(self._http.post("/ads/audiences", body))
        return result if isinstance(result, dict) else {"data": result}

    def search_targeting(
        self,
        *,
        connection_id: str,
        type: str,
        q: str | None = None,
        workspace_id: str | None = None,
    ) -> builtins.list[TargetingOption]:
        """Locations, interests, behaviours and income brackets as Meta names them."""
        return parse_list(
            TargetingOption,
            unwrap(
                self._http.get(
                    "/ads/targeting/search",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "type": type,
                        "q": q,
                    },
                )
            ),
        )

    def lead_forms(self, *, workspace_id: str | None = None) -> builtins.list[LeadFormSource]:
        return parse_list(
            LeadFormSource,
            unwrap(self._http.get("/ads/lead-forms", {"workspace_id": workspace_id})),
        )

    def create_lead_form(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        page_id: str,
        name: str,
        questions: Sequence[str],
        privacy_policy_url: str,
        thank_you_message: str,
        follow_up_url: str | None = None,
    ) -> str:
        """Create an Instant Form on the Page; returns its id."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "pageId": page_id,
            "name": name,
            "questions": list(questions),
            "privacyPolicyUrl": privacy_policy_url,
            "thankYouMessage": thank_you_message,
        }
        if follow_up_url is not None:
            body["followUpUrl"] = follow_up_url
        result = unwrap(self._http.post("/ads/lead-forms", body))
        form_id = result.get("id") if isinstance(result, dict) else None
        return str(form_id) if form_id else ""

    def leads(
        self,
        form_id: str,
        *,
        connection_id: str,
        page_id: str,
        after: str | None = None,
        workspace_id: str | None = None,
    ) -> LeadsPage:
        """One page of leads; pass ``next_cursor`` back as ``after`` for the next."""
        return LeadsPage.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/lead-forms/{form_id}/leads",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "page_id": page_id,
                        "after": after,
                    },
                )
            )
        )
