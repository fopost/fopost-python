"""``client.ads`` — ads, catalogs, audiences, the ad archive and lead forms.

Meta is what this module covers; the Google-only surface is ``client.ads.google``.

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
    AdActivityResult,
    AdCampaign,
    AdConnection,
    AdCreative,
    AdInsightsReport,
    AdLabel,
    AdLibraryPage,
    AdSet,
    AdSource,
    AdStudy,
    Audience,
    AudiencesResult,
    BoostablePost,
    BulkAdStatusResult,
    CatalogBatchResult,
    CatalogProductsPage,
    ExternalAd,
    HighDemandPeriod,
    IosCampaignLimits,
    LeadFormDetail,
    LeadFormSource,
    LeadPage,
    LeadPageSubscription,
    LeadsFeedPage,
    LeadsPage,
    NetworkAd,
    PartnershipCreator,
    ProductCatalog,
    ProductCatalogsResult,
    ProductFeed,
    ProductFeedUpload,
    ProductSet,
    ReachEstimate,
    ReachFrequencyPrediction,
    ReachFrequencyResult,
    TargetingOption,
    ValueRuleSet,
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

    # ─── Goals ─────────────────────────────────────────────────────

    def goals(self, *, connection_id: str, workspace_id: str | None = None) -> builtins.list[str]:
        """The goals this connection's network can run right now.

        Ask rather than assume: a goal the deployment is not set up for is
        absent here and is refused if you send it anyway.
        """
        result = unwrap(
            self._http.get(
                "/ads/goals",
                {"workspace_id": workspace_id, "connection_id": connection_id},
            )
        )
        return [str(goal) for goal in result] if isinstance(result, list) else []

    # ─── Product catalogs ──────────────────────────────────────────

    def catalogs(
        self, *, connection_id: str, workspace_id: str | None = None
    ) -> ProductCatalogsResult:
        """Catalogs the connection's business portfolios reach. Read live, never stored."""
        return ProductCatalogsResult.model_validate(
            unwrap(
                self._http.get(
                    "/ads/catalogs",
                    {"workspace_id": workspace_id, "connection_id": connection_id},
                )
            )
        )

    def create_catalog(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        name: str,
        vertical: str | None = None,
    ) -> ProductCatalog:
        """Created on the connection's business portfolio. Also needs ``publish``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "name": name,
        }
        if vertical is not None:
            body["vertical"] = vertical
        return ProductCatalog.model_validate(unwrap(self._http.post("/ads/catalogs", body)))

    def get_catalog(
        self, catalog_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> ProductCatalog:
        return ProductCatalog.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/catalogs/{catalog_id}",
                    {"workspace_id": workspace_id, "connection_id": connection_id},
                )
            )
        )

    def update_catalog(
        self, catalog_id: str, *, workspace_id: str, connection_id: str, name: str
    ) -> ProductCatalog:
        """Also needs ``publish``."""
        body = {"workspaceId": workspace_id, "connectionId": connection_id, "name": name}
        return ProductCatalog.model_validate(
            unwrap(
                self._http.request(
                    "PATCH",
                    f"/ads/catalogs/{catalog_id}",
                    json=body,
                    params={"workspace_id": workspace_id, "connection_id": connection_id},
                )
            )
        )

    def delete_catalog(self, catalog_id: str, *, workspace_id: str, connection_id: str) -> None:
        """Deletes every product, feed and set in it. Also needs ``publish``."""
        self._http.request(
            "DELETE",
            f"/ads/catalogs/{catalog_id}",
            params={"workspace_id": workspace_id, "connection_id": connection_id},
        )

    def catalog_products(
        self,
        catalog_id: str,
        *,
        connection_id: str,
        workspace_id: str | None = None,
        after: str | None = None,
    ) -> CatalogProductsPage:
        """One page of products; pass ``next_cursor`` back as ``after``."""
        return CatalogProductsPage.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/catalogs/{catalog_id}/products",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "after": after,
                    },
                )
            )
        )

    def write_catalog_products(
        self,
        catalog_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        products: Sequence[Mapping[str, Any]],
    ) -> CatalogBatchResult:
        """Up to 500 upserts and deletes in one batch, keyed by ``retailerId``.

        Also needs ``publish``.
        """
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "products": [dict(p) for p in products],
        }
        return CatalogBatchResult.model_validate(
            unwrap(self._http.post(f"/ads/catalogs/{catalog_id}/products", body))
        )

    def product_feeds(
        self, catalog_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> builtins.list[ProductFeed]:
        return parse_list(
            ProductFeed,
            unwrap(
                self._http.get(
                    f"/ads/catalogs/{catalog_id}/feeds",
                    {"workspace_id": workspace_id, "connection_id": connection_id},
                )
            ),
        )

    def create_product_feed(
        self,
        catalog_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        name: str,
        url: str | None = None,
        schedule: str | None = None,
    ) -> ProductFeed:
        """``schedule`` is ``HOURLY``, ``DAILY`` or ``WEEKLY`` and needs ``url``.

        Also needs ``publish``.
        """
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "name": name,
        }
        optional = {"url": url, "schedule": schedule}
        body.update({k: v for k, v in optional.items() if v is not None})
        return ProductFeed.model_validate(
            unwrap(self._http.post(f"/ads/catalogs/{catalog_id}/feeds", body))
        )

    def delete_product_feed(
        self, catalog_id: str, feed_id: str, *, workspace_id: str, connection_id: str
    ) -> None:
        """Also needs ``publish``."""
        self._http.request(
            "DELETE",
            f"/ads/catalogs/{catalog_id}/feeds/{feed_id}",
            params={"workspace_id": workspace_id, "connection_id": connection_id},
        )

    def feed_uploads(
        self,
        catalog_id: str,
        feed_id: str,
        *,
        connection_id: str,
        workspace_id: str | None = None,
    ) -> builtins.list[ProductFeedUpload]:
        """Each run the network made of the feed."""
        return parse_list(
            ProductFeedUpload,
            unwrap(
                self._http.get(
                    f"/ads/catalogs/{catalog_id}/feeds/{feed_id}/uploads",
                    {"workspace_id": workspace_id, "connection_id": connection_id},
                )
            ),
        )

    def start_feed_upload(
        self,
        catalog_id: str,
        feed_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        url: str | None = None,
    ) -> str:
        """Fetches the feed now; the id of the run. Also needs ``publish``."""
        body: dict[str, Any] = {"workspaceId": workspace_id, "connectionId": connection_id}
        if url is not None:
            body["url"] = url
        result = unwrap(
            self._http.post(f"/ads/catalogs/{catalog_id}/feeds/{feed_id}/uploads", body)
        )
        upload_id = result.get("id") if isinstance(result, dict) else None
        return str(upload_id) if upload_id else ""

    def product_sets(
        self, catalog_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> builtins.list[ProductSet]:
        """A catalog ad runs from a product set, not the whole catalog."""
        return parse_list(
            ProductSet,
            unwrap(
                self._http.get(
                    f"/ads/catalogs/{catalog_id}/product-sets",
                    {"workspace_id": workspace_id, "connection_id": connection_id},
                )
            ),
        )

    def create_product_set(
        self,
        catalog_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        name: str,
        filter: Mapping[str, Any] | None = None,
    ) -> ProductSet:
        """Without a ``filter`` the set is the whole catalog. Also needs ``publish``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "name": name,
        }
        if filter is not None:
            body["filter"] = dict(filter)
        return ProductSet.model_validate(
            unwrap(self._http.post(f"/ads/catalogs/{catalog_id}/product-sets", body))
        )

    def update_product_set(
        self,
        catalog_id: str,
        set_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        name: str,
        filter: Mapping[str, Any] | None = None,
    ) -> ProductSet:
        """Also needs ``publish``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "name": name,
        }
        if filter is not None:
            body["filter"] = dict(filter)
        return ProductSet.model_validate(
            unwrap(
                self._http.request(
                    "PATCH",
                    f"/ads/catalogs/{catalog_id}/product-sets/{set_id}",
                    json=body,
                    params={"workspace_id": workspace_id, "connection_id": connection_id},
                )
            )
        )

    def delete_product_set(
        self, catalog_id: str, set_id: str, *, workspace_id: str, connection_id: str
    ) -> None:
        """Also needs ``publish``."""
        self._http.request(
            "DELETE",
            f"/ads/catalogs/{catalog_id}/product-sets/{set_id}",
            params={"workspace_id": workspace_id, "connection_id": connection_id},
        )

    # ─── Reach and frequency ───────────────────────────────────────

    def reach_frequency(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> ReachFrequencyResult:
        return ReachFrequencyResult.model_validate(
            unwrap(
                self._http.get(
                    "/ads/reach-frequency",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "ad_account_id": ad_account_id,
                    },
                )
            )
        )

    def create_reach_frequency(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str,
        targeting: Mapping[str, Any],
        placements: Sequence[str],
        budget_minor: int,
        start_at: str,
        end_at: str,
        frequency_cap: int | None = None,
    ) -> ReachFrequencyPrediction:
        """Prices a flight. Nothing is bought until you reserve it."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "name": name,
            "targeting": dict(targeting),
            "placements": list(placements),
            "budgetMinor": budget_minor,
            "startAt": start_at,
            "endAt": end_at,
        }
        if frequency_cap is not None:
            body["frequencyCap"] = frequency_cap
        return ReachFrequencyPrediction.model_validate(
            unwrap(self._http.post("/ads/reach-frequency", body))
        )

    def get_reach_frequency(
        self,
        prediction_id: str,
        *,
        connection_id: str,
        ad_account_id: str,
        workspace_id: str | None = None,
    ) -> ReachFrequencyPrediction:
        return ReachFrequencyPrediction.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/reach-frequency/{prediction_id}",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "ad_account_id": ad_account_id,
                    },
                )
            )
        )

    def reserve_reach_frequency(
        self, prediction_id: str, *, workspace_id: str, connection_id: str, ad_account_id: str
    ) -> ReachFrequencyPrediction:
        """Holds the inventory the prediction priced. Also needs ``publish``."""
        return self._reach_frequency_action(
            prediction_id, "reserve", workspace_id, connection_id, ad_account_id
        )

    def cancel_reach_frequency(
        self, prediction_id: str, *, workspace_id: str, connection_id: str, ad_account_id: str
    ) -> ReachFrequencyPrediction:
        """Also needs ``publish``."""
        return self._reach_frequency_action(
            prediction_id, "cancel", workspace_id, connection_id, ad_account_id
        )

    # ─── Ad Library ────────────────────────────────────────────────

    def library(
        self,
        *,
        connection_id: str,
        countries: Sequence[str],
        workspace_id: str | None = None,
        q: str | None = None,
        page_ids: Sequence[str] | None = None,
        active_status: str | None = None,
        limit: int | None = None,
        after: str | None = None,
    ) -> AdLibraryPage:
        """The public ad archive: ads anyone is running, by keyword or by Page.

        Read live on every call and stored nowhere, so an ad that stops running
        is simply absent from the next search. Search by ``q`` or ``page_ids``.
        """
        params: dict[str, Any] = {
            "workspace_id": workspace_id,
            "connection_id": connection_id,
            "countries": ",".join(countries),
            "q": q,
            "page_ids": ",".join(page_ids) if page_ids else None,
            "active_status": active_status,
            "limit": limit,
            "after": after,
        }
        return AdLibraryPage.model_validate(unwrap(self._http.get("/ads/library", params)))

    # ─── Partnership ads ───────────────────────────────────────────

    def partnership_creators(
        self, *, connection_id: str, page_id: str, workspace_id: str | None = None
    ) -> builtins.list[PartnershipCreator]:
        """Creators who allowlisted this Page to run partnership ads on their posts."""
        return parse_list(
            PartnershipCreator,
            unwrap(
                self._http.get(
                    "/ads/partnership/creators",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "page_id": page_id,
                    },
                )
            ),
        )

    def request_partnership(
        self, *, workspace_id: str, connection_id: str, page_id: str, creator_id: str
    ) -> builtins.list[PartnershipCreator]:
        """Asks a creator for permission; the list as it now stands."""
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "pageId": page_id,
            "creatorId": creator_id,
        }
        return parse_list(
            PartnershipCreator, unwrap(self._http.post("/ads/partnership/creators", body))
        )

    def revoke_partnership(
        self, creator_id: str, *, workspace_id: str, connection_id: str, page_id: str
    ) -> None:
        self._http.request(
            "DELETE",
            f"/ads/partnership/creators/{creator_id}",
            params={
                "workspace_id": workspace_id,
                "connection_id": connection_id,
                "page_id": page_id,
            },
        )

    # ─── Ad account settings ───────────────────────────────────────

    def account_activity(
        self,
        *,
        connection_id: str,
        ad_account_id: str,
        workspace_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> AdActivityResult:
        """Who changed what on the ad account, and when. Dates are ``YYYY-MM-DD``."""
        params = self._account_params(workspace_id, connection_id, ad_account_id)
        params.update({"since": since, "until": until})
        return AdActivityResult.model_validate(
            unwrap(self._http.get("/ads/account/activity", params))
        )

    def labels(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[AdLabel]:
        return parse_list(
            AdLabel,
            unwrap(
                self._http.get(
                    "/ads/account/labels",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            ),
        )

    def create_label(
        self, *, workspace_id: str, connection_id: str, ad_account_id: str, name: str
    ) -> AdLabel:
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "name": name,
        }
        return AdLabel.model_validate(unwrap(self._http.post("/ads/account/labels", body)))

    def update_label(
        self,
        label_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str,
    ) -> AdLabel:
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "name": name,
        }
        return AdLabel.model_validate(
            unwrap(
                self._http.request(
                    "PATCH",
                    f"/ads/account/labels/{label_id}",
                    json=body,
                    params={"workspace_id": workspace_id, "connection_id": connection_id},
                )
            )
        )

    def delete_label(
        self, label_id: str, *, workspace_id: str, connection_id: str, ad_account_id: str
    ) -> None:
        self._http.request(
            "DELETE",
            f"/ads/account/labels/{label_id}",
            params=self._account_params(workspace_id, connection_id, ad_account_id),
        )

    def apply_label(
        self,
        label_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        object_id: str,
        level: str,
    ) -> None:
        """Keeps whatever labels the object already carries. ``level`` is
        ``campaign``, ``ad_set`` or ``ad``.
        """
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "objectId": object_id,
            "level": level,
        }
        self._http.post(f"/ads/account/labels/{label_id}/apply", body)

    def studies(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[AdStudy]:
        return parse_list(
            AdStudy,
            unwrap(
                self._http.get(
                    "/ads/account/studies",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            ),
        )

    def create_study(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str,
        start_at: str,
        end_at: str,
        cells: Sequence[Mapping[str, Any]],
        description: str | None = None,
    ) -> AdStudy:
        """Splits traffic evenly across two to five ``cells`` of ``name`` and ``objectIds``."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "name": name,
            "startAt": start_at,
            "endAt": end_at,
            "cells": [dict(c) for c in cells],
        }
        if description is not None:
            body["description"] = description
        return AdStudy.model_validate(unwrap(self._http.post("/ads/account/studies", body)))

    def get_study(
        self,
        study_id: str,
        *,
        connection_id: str,
        ad_account_id: str,
        workspace_id: str | None = None,
    ) -> AdStudy:
        return AdStudy.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/account/studies/{study_id}",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            )
        )

    def delete_study(
        self, study_id: str, *, workspace_id: str, connection_id: str, ad_account_id: str
    ) -> None:
        self._http.request(
            "DELETE",
            f"/ads/account/studies/{study_id}",
            params=self._account_params(workspace_id, connection_id, ad_account_id),
        )

    def ios_campaign_limits(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[IosCampaignLimits]:
        """How many iOS 14 campaigns the account may run at once, per app."""
        return parse_list(
            IosCampaignLimits,
            unwrap(
                self._http.get(
                    "/ads/account/ios-limits",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            ),
        )

    def high_demand_periods(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[HighDemandPeriod]:
        return parse_list(
            HighDemandPeriod,
            unwrap(
                self._http.get(
                    "/ads/account/high-demand-periods",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            ),
        )

    def create_high_demand_period(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        start_at: str,
        end_at: str,
        budget_value: float,
        budget_value_type: str,
    ) -> HighDemandPeriod:
        """Tells the network to expect heavier spend over a window, so pacing allows for it.

        ``budget_value_type`` is ``ABSOLUTE`` or ``MULTIPLIER``.
        """
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "startAt": start_at,
            "endAt": end_at,
            "budgetValue": budget_value,
            "budgetValueType": budget_value_type,
        }
        return HighDemandPeriod.model_validate(
            unwrap(self._http.post("/ads/account/high-demand-periods", body))
        )

    def delete_high_demand_period(
        self, period_id: str, *, workspace_id: str, connection_id: str, ad_account_id: str
    ) -> None:
        self._http.request(
            "DELETE",
            f"/ads/account/high-demand-periods/{period_id}",
            params=self._account_params(workspace_id, connection_id, ad_account_id),
        )

    def value_rule_sets(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[ValueRuleSet]:
        return parse_list(
            ValueRuleSet,
            unwrap(
                self._http.get(
                    "/ads/account/value-rule-sets",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            ),
        )

    def create_value_rule_set(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str,
        rules: Sequence[Mapping[str, Any]],
    ) -> ValueRuleSet:
        """Weights conversions so some audiences count for more than others."""
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "name": name,
            "rules": [dict(r) for r in rules],
        }
        return ValueRuleSet.model_validate(
            unwrap(self._http.post("/ads/account/value-rule-sets", body))
        )

    def delete_value_rule_set(
        self, rule_set_id: str, *, workspace_id: str, connection_id: str, ad_account_id: str
    ) -> None:
        self._http.request(
            "DELETE",
            f"/ads/account/value-rule-sets/{rule_set_id}",
            params=self._account_params(workspace_id, connection_id, ad_account_id),
        )

    @staticmethod
    def _account_params(
        workspace_id: str | None, connection_id: str, ad_account_id: str
    ) -> dict[str, Any]:
        return {
            "workspace_id": workspace_id,
            "connection_id": connection_id,
            "ad_account_id": ad_account_id,
        }

    def _reach_frequency_action(
        self,
        prediction_id: str,
        action: str,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
    ) -> ReachFrequencyPrediction:
        body = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
        }
        return ReachFrequencyPrediction.model_validate(
            unwrap(self._http.post(f"/ads/reach-frequency/{prediction_id}/{action}", body))
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
