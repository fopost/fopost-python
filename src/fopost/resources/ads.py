"""``client.ads`` — ads, audiences and lead forms across the ad networks.

Every method needs the ``ads`` scope; ``boost``, ``create``, ``set_status``,
``delete``, ``bulk_set_status`` and every create, update, delete or duplicate on
campaigns, ad sets and network ads spend money and also need ``publish``.
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    Ad,
    AdAccountTree,
    AdCampaign,
    AdConnection,
    AdCreative,
    AdInsightsReport,
    AdSet,
    AdSource,
    Audience,
    AudiencesResult,
    BoostablePost,
    BulkAdStatusResult,
    ExternalAd,
    LeadFormDetail,
    LeadFormSource,
    LeadPage,
    LeadPageSubscription,
    LeadsFeedPage,
    LeadsPage,
    NetworkAd,
    ReachEstimate,
    TargetingOption,
)
from ._base import UNSET, Resource, drop_unset, parse_list
from .google_ads import GoogleAdsResource

__all__ = ["AdsResource"]


class AdsResource(Resource):
    def __init__(self, http: Any) -> None:
        super().__init__(http)
        #: The Search surface no other network has: keywords, assets, conversions, GAQL.
        self.google = GoogleAdsResource(http)

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

    def authorize_google(self, *, workspace_id: str, return_to: str | None = None) -> str:
        """The Google login URL; the caller finishes it in their own browser."""
        body: dict[str, Any] = {"workspaceId": workspace_id}
        if return_to is not None:
            body["returnTo"] = return_to
        result = unwrap(self._http.post("/ads/connections/google/authorize", body))
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
        url_tags: str | None = None,
        paused: bool | None = None,
    ) -> Ad:
        """Create a standalone ad from a creative. Starts paused unless ``paused=False``.

        ``url_tags`` is a query string appended to every link, e.g. ``utm_source=meta``.
        """
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
            "urlTags": url_tags,
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

    # ─── Campaign tree (Meta ids, read live, never stored) ──────────────

    def account_tree(
        self, ad_account_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> AdAccountTree:
        """Every campaign on the ad account with its ad sets and their ads."""
        return AdAccountTree.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/accounts/{ad_account_id}/tree",
                    {"workspace_id": workspace_id, "connection_id": connection_id},
                )
            )
        )

    def create_campaign(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str,
        goal: str,
        paused: bool | None = None,
    ) -> AdCampaign:
        """Starts paused unless ``paused=False``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "name": name,
            "goal": goal,
        }
        if paused is not None:
            body["paused"] = paused
        return AdCampaign.model_validate(unwrap(self._http.post("/ads/campaigns", body)))

    def get_campaign(
        self, campaign_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> AdCampaign:
        return AdCampaign.model_validate(
            unwrap(self._object("GET", "campaigns", campaign_id, workspace_id, connection_id))
        )

    def update_campaign(
        self,
        campaign_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        name: str | Any = UNSET,
        status: str | Any = UNSET,
    ) -> AdCampaign:
        """Partial update; ``status`` is ``active`` or ``paused``."""
        body = drop_unset({"name": name, "status": status})
        return AdCampaign.model_validate(
            unwrap(
                self._object("PATCH", "campaigns", campaign_id, workspace_id, connection_id, body)
            )
        )

    def delete_campaign(self, campaign_id: str, *, workspace_id: str, connection_id: str) -> None:
        self._object("DELETE", "campaigns", campaign_id, workspace_id, connection_id)

    def duplicate_campaign(
        self,
        campaign_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        paused: bool | None = None,
    ) -> str:
        """Copy the campaign with its ad sets and ads; returns the copy's Meta id."""
        return self._duplicate("campaigns", campaign_id, workspace_id, connection_id, paused)

    def create_ad_set(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        campaign_id: str,
        page_id: str,
        name: str,
        goal: str,
        budget: Mapping[str, Any],
        targeting: Mapping[str, Any],
        paused: bool | None = None,
    ) -> AdSet:
        """Starts paused unless ``paused=False``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "campaignId": campaign_id,
            "pageId": page_id,
            "name": name,
            "goal": goal,
            "budget": dict(budget),
            "targeting": dict(targeting),
        }
        if paused is not None:
            body["paused"] = paused
        return AdSet.model_validate(unwrap(self._http.post("/ads/ad-sets", body)))

    def get_ad_set(
        self, ad_set_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> AdSet:
        return AdSet.model_validate(
            unwrap(self._object("GET", "ad-sets", ad_set_id, workspace_id, connection_id))
        )

    def update_ad_set(
        self,
        ad_set_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        name: str | Any = UNSET,
        status: str | Any = UNSET,
        budget_minor: int | Any = UNSET,
        end_at: str | Any = UNSET,
        targeting: Mapping[str, Any] | Any = UNSET,
    ) -> AdSet:
        """Partial update. The budget type set at creation stays."""
        body = drop_unset(
            {
                "name": name,
                "status": status,
                "budgetMinor": budget_minor,
                "endAt": end_at,
                "targeting": dict(targeting) if targeting is not UNSET else UNSET,
            }
        )
        return AdSet.model_validate(
            unwrap(self._object("PATCH", "ad-sets", ad_set_id, workspace_id, connection_id, body))
        )

    def delete_ad_set(self, ad_set_id: str, *, workspace_id: str, connection_id: str) -> None:
        self._object("DELETE", "ad-sets", ad_set_id, workspace_id, connection_id)

    def duplicate_ad_set(
        self,
        ad_set_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        paused: bool | None = None,
    ) -> str:
        """Returns the copy's Meta id."""
        return self._duplicate("ad-sets", ad_set_id, workspace_id, connection_id, paused)

    def create_network_ad(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_set_id: str,
        creative_id: str,
        name: str,
        paused: bool | None = None,
    ) -> NetworkAd:
        """An ad inside an ad set, from a creative. Starts paused unless ``paused=False``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adSetId": ad_set_id,
            "creativeId": creative_id,
            "name": name,
        }
        if paused is not None:
            body["paused"] = paused
        return NetworkAd.model_validate(unwrap(self._http.post("/ads/ads", body)))

    def get_network_ad(
        self, ad_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> NetworkAd:
        return NetworkAd.model_validate(
            unwrap(self._object("GET", "ads", ad_id, workspace_id, connection_id))
        )

    def update_network_ad(
        self,
        ad_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        name: str | Any = UNSET,
        status: str | Any = UNSET,
        creative_id: str | Any = UNSET,
    ) -> NetworkAd:
        """Partial update; ``creative_id`` swaps the ad's creative."""
        body = drop_unset({"name": name, "status": status, "creativeId": creative_id})
        return NetworkAd.model_validate(
            unwrap(self._object("PATCH", "ads", ad_id, workspace_id, connection_id, body))
        )

    def delete_network_ad(self, ad_id: str, *, workspace_id: str, connection_id: str) -> None:
        self._object("DELETE", "ads", ad_id, workspace_id, connection_id)

    def duplicate_network_ad(
        self,
        ad_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        paused: bool | None = None,
    ) -> str:
        """Returns the copy's Meta id."""
        return self._duplicate("ads", ad_id, workspace_id, connection_id, paused)

    def bulk_set_status(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        status: str,
        objects: Sequence[Mapping[str, str]],
    ) -> builtins.list[BulkAdStatusResult]:
        """Pause or resume many objects at once.

        ``objects`` holds ``{"id": ..., "level": "campaign" | "ad_set" | "ad"}``; each
        result reports its own ``ok`` and ``error``.
        """
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "status": status,
            "objects": [dict(o) for o in objects],
        }
        return parse_list(BulkAdStatusResult, unwrap(self._http.post("/ads/status", body)))

    # ─── Creatives ──────────────────────────────────────────────────────

    def creatives(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[AdCreative]:
        result = unwrap(
            self._http.get(
                "/ads/creatives",
                {
                    "workspace_id": workspace_id,
                    "connection_id": connection_id,
                    "ad_account_id": ad_account_id,
                },
            )
        )
        return parse_list(AdCreative, result.get("creatives") if isinstance(result, dict) else None)

    def create_creative(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        page_id: str,
        name: str,
        format: str,
        text: str,
        headline: str | None = None,
        destination_url: str | None = None,
        call_to_action: str | None = None,
        url_tags: str | None = None,
        media_url: str | None = None,
        thumbnail_media_url: str | None = None,
        cards: Sequence[Mapping[str, Any]] | None = None,
    ) -> AdCreative:
        """``format`` is ``image``, ``video`` (needs ``media_url``) or ``carousel`` (needs
        2-10 ``cards`` of ``mediaUrl``, ``destinationUrl``, ``headline``, ``description``).
        """
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "pageId": page_id,
            "name": name,
            "format": format,
            "text": text,
        }
        optional = {
            "headline": headline,
            "destinationUrl": destination_url,
            "callToAction": call_to_action,
            "urlTags": url_tags,
            "mediaUrl": media_url,
            "thumbnailMediaUrl": thumbnail_media_url,
            "cards": [dict(c) for c in cards] if cards is not None else None,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return AdCreative.model_validate(unwrap(self._http.post("/ads/creatives", body)))

    def get_creative(
        self, creative_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> AdCreative:
        return AdCreative.model_validate(
            unwrap(self._object("GET", "creatives", creative_id, workspace_id, connection_id))
        )

    def delete_creative(self, creative_id: str, *, workspace_id: str, connection_id: str) -> None:
        self._object("DELETE", "creatives", creative_id, workspace_id, connection_id)

    # ─── Audiences ──────────────────────────────────────────────────────

    def get_audience(
        self, audience_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> Audience:
        return Audience.model_validate(
            unwrap(self._object("GET", "audiences", audience_id, workspace_id, connection_id))
        )

    def update_audience(
        self,
        audience_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        name: str | Any = UNSET,
        description: str | Any = UNSET,
    ) -> Audience:
        body = drop_unset({"name": name, "description": description})
        return Audience.model_validate(
            unwrap(
                self._object("PATCH", "audiences", audience_id, workspace_id, connection_id, body)
            )
        )

    def delete_audience(self, audience_id: str, *, workspace_id: str, connection_id: str) -> None:
        self._object("DELETE", "audiences", audience_id, workspace_id, connection_id)

    def add_audience_users(
        self,
        audience_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        emails: Sequence[str],
    ) -> int:
        """Add people to a custom audience; the API hashes the emails. Returns the count sent."""
        result = unwrap(
            self._http.request(
                "POST",
                f"/ads/audiences/{audience_id}/users",
                json={"emails": list(emails)},
                params={"workspace_id": workspace_id, "connection_id": connection_id},
            )
        )
        added = result.get("added") if isinstance(result, dict) else None
        return int(added) if added is not None else 0

    # ─── Reach and insights ─────────────────────────────────────────────

    def estimate_reach(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        page_id: str,
        targeting: Mapping[str, Any],
    ) -> ReachEstimate:
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "pageId": page_id,
            "targeting": dict(targeting),
        }
        return ReachEstimate.model_validate(unwrap(self._http.post("/ads/reach-estimate", body)))

    def insights(
        self,
        *,
        connection_id: str,
        object_id: str,
        since: str,
        until: str,
        breakdown: str | None = None,
        daily: bool | None = None,
        workspace_id: str | None = None,
    ) -> AdInsightsReport:
        """Insights for any Meta campaign, ad set or ad id.

        ``breakdown`` is ``age``, ``gender``, ``placement`` or ``country``; ``daily`` adds a
        per-day timeline.
        """
        return AdInsightsReport.model_validate(
            unwrap(
                self._http.get(
                    "/ads/insights",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "object_id": object_id,
                        "since": since,
                        "until": until,
                        "breakdown": breakdown,
                        "daily": daily,
                    },
                )
            )
        )

    def ad_insights(
        self,
        ad_id: str,
        *,
        workspace_id: str,
        since: str,
        until: str,
        breakdown: str | None = None,
        daily: bool | None = None,
    ) -> AdInsightsReport:
        """Insights for an ad created through FoPost, by its FoPost id."""
        return AdInsightsReport.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/{ad_id}/insights",
                    {
                        "workspace_id": workspace_id,
                        "since": since,
                        "until": until,
                        "breakdown": breakdown,
                        "daily": daily,
                    },
                )
            )
        )

    # ─── Lead forms and the leads feed ──────────────────────────────────

    def get_lead_form(
        self,
        form_id: str,
        *,
        connection_id: str,
        page_id: str,
        workspace_id: str | None = None,
    ) -> LeadFormDetail:
        return LeadFormDetail.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/lead-forms/{form_id}",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "page_id": page_id,
                    },
                )
            )
        )

    def archive_lead_form(
        self, form_id: str, *, workspace_id: str, connection_id: str, page_id: str
    ) -> LeadFormDetail:
        body = {"workspaceId": workspace_id, "connectionId": connection_id, "pageId": page_id}
        return LeadFormDetail.model_validate(
            unwrap(self._http.post(f"/ads/lead-forms/{form_id}/archive", body))
        )

    def leads_feed(
        self,
        *,
        workspace_id: str | None = None,
        form_id: str | None = None,
        page_id: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> LeadsFeedPage:
        """Leads stored from subscribed Pages, newest first.

        Pass ``next_cursor`` back as ``cursor`` for the next page.
        """
        return LeadsFeedPage.model_validate(
            unwrap(
                self._http.get(
                    "/ads/leads",
                    {
                        "workspace_id": workspace_id,
                        "form_id": form_id,
                        "page_id": page_id,
                        "cursor": cursor,
                        "limit": limit,
                    },
                )
            )
        )

    def lead_pages(self, *, workspace_id: str | None = None) -> builtins.list[LeadPage]:
        """Pages whose leads FoPost stores."""
        return parse_list(
            LeadPage, unwrap(self._http.get("/ads/lead-pages", {"workspace_id": workspace_id}))
        )

    def subscribe_lead_page(
        self, *, workspace_id: str, connection_id: str, page_id: str
    ) -> LeadPageSubscription:
        """Start storing the Page's leads; leads already there are backfilled."""
        body = {"workspaceId": workspace_id, "connectionId": connection_id, "pageId": page_id}
        return LeadPageSubscription.model_validate(unwrap(self._http.post("/ads/lead-pages", body)))

    def unsubscribe_lead_page(self, page_id: str, *, workspace_id: str, connection_id: str) -> None:
        self._http.request(
            "DELETE",
            f"/ads/lead-pages/{page_id}",
            params={"workspace_id": workspace_id, "connection_id": connection_id},
        )

    def _object(
        self,
        method: str,
        kind: str,
        object_id: str,
        workspace_id: str | None,
        connection_id: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        return self._http.request(
            method,
            f"/ads/{kind}/{object_id}",
            json=body,
            params={"workspace_id": workspace_id, "connection_id": connection_id},
        )

    def _duplicate(
        self,
        kind: str,
        object_id: str,
        workspace_id: str,
        connection_id: str,
        paused: bool | None,
    ) -> str:
        result = unwrap(
            self._http.request(
                "POST",
                f"/ads/{kind}/{object_id}/duplicate",
                json={"paused": paused} if paused is not None else {},
                params={"workspace_id": workspace_id, "connection_id": connection_id},
            )
        )
        copy_id = result.get("id") if isinstance(result, dict) else None
        return str(copy_id) if copy_id else ""
