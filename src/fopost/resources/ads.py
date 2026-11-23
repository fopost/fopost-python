"""``client.ads`` — ads, audiences, lead forms and ad comments.

The connection decides which network a call reaches, so the same methods run
Meta and TikTok; the Google-only surface is ``client.ads.google``.

Every method needs the ``ads`` scope; ``boost``, ``create``, ``set_status``,
``delete`` and ``bulk_set_status`` spend money and also need ``publish``.
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    Ad,
    AdActivityResult,
    AdBusinessCenter,
    AdCommentsPage,
    AdConnection,
    AdIdentity,
    AdInsightsReport,
    AdLabel,
    AdPixel,
    AdPixelDetail,
    AdProvider,
    AdSource,
    AdStudy,
    Audience,
    AudiencesResult,
    BidPricing,
    BoostablePost,
    BulkAdStatusResult,
    ConversionBatch,
    ConversionMetrics,
    ConversionRule,
    ConversionUploadResult,
    CustomConversion,
    EventMatchQuality,
    ExternalAd,
    HighDemandPeriod,
    IosCampaignLimits,
    LeadFormDetail,
    LeadFormSource,
    LeadPage,
    LeadPageSubscription,
    LeadsFeedPage,
    LeadsPage,
    PartnershipCreator,
    PixelStats,
    ReachEstimate,
    ReachFrequencyPrediction,
    ReachFrequencyResult,
    SparkPost,
    SupplyForecast,
    TargetingOption,
    ValueRuleSet,
)
from ._base import UNSET, Resource, drop_unset, parse_list
from .google_ads import GoogleAdsResource

__all__ = ["AdsResource"]


class AdsResource(Resource):
    def __init__(self, http: Any) -> None:
        super().__init__(http)
        #: The Search surface no other network has: bid strategies, conversions, GAQL.
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

    def providers(self) -> builtins.list[AdProvider]:
        """The ad networks this deployment knows, with what each one supports."""
        return parse_list(AdProvider, unwrap(self._http.get("/ads/providers")))

    def authorize(
        self,
        provider: str,
        *,
        workspace_id: str,
        method: str | None = None,
        return_to: str | None = None,
    ) -> str:
        """The network's login URL; the caller finishes it in their own browser."""
        body: dict[str, Any] = {"workspaceId": workspace_id}
        if method is not None:
            body["method"] = method
        if return_to is not None:
            body["returnTo"] = return_to
        result = unwrap(self._http.post(f"/ads/connections/{provider}/authorize", body))
        url = result.get("url") if isinstance(result, dict) else None
        return str(url) if url else ""

    def authorize_meta(
        self, *, workspace_id: str, method: str | None = None, return_to: str | None = None
    ) -> str:
        """Deprecated: use ``authorize("meta", ...)``."""
        return self.authorize("meta", workspace_id=workspace_id, method=method, return_to=return_to)

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
        spark_post_id: str | None = None,
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
            "sparkPostId": spark_post_id,
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

    def add_audience_companies(
        self,
        audience_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        companies: Sequence[Mapping[str, Any]],
    ) -> int:
        """Add companies to a company-list audience. Returns the count the network took.

        Each row needs a ``name``, ``domain``, ``pageUrl`` or ``ticker``. The rows
        travel with the request and are never stored.
        """
        result = unwrap(
            self._http.request(
                "POST",
                f"/ads/audiences/{audience_id}/companies",
                json={"companies": [dict(c) for c in companies]},
                params={"workspace_id": workspace_id, "connection_id": connection_id},
            )
        )
        added = result.get("added") if isinstance(result, dict) else None
        return int(added) if added is not None else 0

    # ─── Forecasts and conversions ──────────────────────────────────────

    def bid_pricing(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        goal: str,
        targeting: Mapping[str, Any],
        placements: Sequence[str] | None = None,
        bid_type: str | None = None,
    ) -> BidPricing:
        """What the auction currently costs for that audience."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "goal": goal,
            "targeting": dict(targeting),
        }
        if placements is not None:
            body["placements"] = list(placements)
        if bid_type is not None:
            body["bidType"] = bid_type
        return BidPricing.model_validate(unwrap(self._http.post("/ads/linkedin/bid-pricing", body)))

    def supply_forecast(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        goal: str,
        targeting: Mapping[str, Any],
        placements: Sequence[str] | None = None,
        budget_minor: int | None = None,
    ) -> SupplyForecast:
        """What that audience would deliver at that budget."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "connectionId": connection_id,
            "adAccountId": ad_account_id,
            "goal": goal,
            "targeting": dict(targeting),
        }
        if placements is not None:
            body["placements"] = list(placements)
        if budget_minor is not None:
            body["budgetMinor"] = budget_minor
        return SupplyForecast.model_validate(
            unwrap(self._http.post("/ads/linkedin/supply-forecast", body))
        )

    def conversion_rules(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[ConversionRule]:
        return parse_list(
            ConversionRule,
            unwrap(
                self._http.get(
                    "/ads/linkedin/conversion-rules",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "ad_account_id": ad_account_id,
                    },
                )
            ),
        )

    def create_conversion_rule(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str,
        type: str,
        attribution: str,
        post_click_window_days: int | None = None,
        view_through_window_days: int | None = None,
        value_minor: int | None = None,
        currency: str | None = None,
    ) -> str:
        body = drop_unset(
            {
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adAccountId": ad_account_id,
                "name": name,
                "type": type,
                "attribution": attribution,
                "postClickWindowDays": post_click_window_days
                if post_click_window_days is not None
                else UNSET,
                "viewThroughWindowDays": view_through_window_days
                if view_through_window_days is not None
                else UNSET,
                "valueMinor": value_minor if value_minor is not None else UNSET,
                "currency": currency if currency is not None else UNSET,
            }
        )
        result = unwrap(self._http.post("/ads/linkedin/conversion-rules", body))
        rule_id = result.get("id") if isinstance(result, dict) else None
        return str(rule_id) if rule_id else ""

    def get_conversion_rule(
        self, rule_id: str, *, connection_id: str, workspace_id: str | None = None
    ) -> ConversionRule:
        return ConversionRule.model_validate(
            unwrap(self._rule("GET", rule_id, "", workspace_id, connection_id))
        )

    def update_conversion_rule(
        self, rule_id: str, *, workspace_id: str, connection_id: str, **changes: Any
    ) -> ConversionRule:
        """Change a rule. Keys are the API's own: ``name``, ``type``, ``attribution``,
        ``postClickWindowDays``, ``viewThroughWindowDays``, ``valueMinor``, ``currency``,
        ``enabled``."""
        return ConversionRule.model_validate(
            unwrap(self._rule("PATCH", rule_id, "", workspace_id, connection_id, changes))
        )

    def delete_conversion_rule(
        self, rule_id: str, *, workspace_id: str, connection_id: str
    ) -> None:
        """Turns the rule off; the network keeps the history."""
        self._rule("DELETE", rule_id, "", workspace_id, connection_id)

    def attach_conversion_rule(
        self, rule_id: str, *, workspace_id: str, connection_id: str, campaign_id: str
    ) -> ConversionRule:
        return ConversionRule.model_validate(
            unwrap(
                self._rule(
                    "POST",
                    rule_id,
                    "/associations",
                    workspace_id,
                    connection_id,
                    {"campaignId": campaign_id},
                )
            )
        )

    def detach_conversion_rule(
        self, rule_id: str, *, workspace_id: str, connection_id: str, campaign_id: str
    ) -> ConversionRule:
        return ConversionRule.model_validate(
            unwrap(
                self._rule(
                    "DELETE",
                    rule_id,
                    "/associations",
                    workspace_id,
                    connection_id,
                    {"campaignId": campaign_id},
                )
            )
        )

    def conversion_metrics(
        self,
        rule_id: str,
        *,
        connection_id: str,
        since: str,
        until: str,
        workspace_id: str | None = None,
    ) -> ConversionMetrics:
        return ConversionMetrics.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/linkedin/conversion-rules/{rule_id}/metrics",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "since": since,
                        "until": until,
                    },
                )
            )
        )

    def send_conversion_events(
        self,
        rule_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        events: Sequence[Mapping[str, Any]],
    ) -> int:
        """Send conversions back to the network. Returns how many it took.

        Each event needs ``happenedAt`` in epoch milliseconds and an ``email`` or a
        ``clickId``. The address is hashed inside the API and nothing is stored.
        """
        result = unwrap(
            self._rule(
                "POST",
                rule_id,
                "/events",
                workspace_id,
                connection_id,
                {"events": [dict(e) for e in events]},
            )
        )
        accepted = result.get("accepted") if isinstance(result, dict) else None
        return int(accepted) if accepted is not None else 0

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

    def tiktok_business_centers(
        self, *, connection_id: str, workspace_id: str | None = None
    ) -> builtins.list[AdBusinessCenter]:
        """TikTok's Business Centers, the one network-named read in this resource."""
        return parse_list(
            AdBusinessCenter,
            unwrap(
                self._http.get(
                    "/ads/tiktok/business-centers",
                    {"workspace_id": workspace_id, "connection_id": connection_id},
                )
            ),
        )

    def tiktok_identities(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[AdIdentity]:
        """The accounts an ad can run as; an identity id is a ``page_id``."""
        return parse_list(
            AdIdentity,
            unwrap(
                self._http.get(
                    "/ads/tiktok/identities",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "ad_account_id": ad_account_id,
                    },
                )
            ),
        )

    def spark_posts(
        self,
        *,
        connection_id: str,
        ad_account_id: str,
        identity_id: str,
        workspace_id: str | None = None,
    ) -> builtins.list[SparkPost]:
        """Posts already live under an identity, each a candidate Spark ad."""
        return parse_list(
            SparkPost,
            unwrap(
                self._http.get(
                    "/ads/spark-posts",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "ad_account_id": ad_account_id,
                        "identity_id": identity_id,
                    },
                )
            ),
        )

    def upload_conversions(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        pixel_id: str,
        events: Sequence[Mapping[str, Any]],
        idempotency_key: str | None = None,
    ) -> ConversionUploadResult:
        """Offline conversions. Identifiers are hashed before they leave FoPost.

        Each event is the API's own shape: ``eventName``, ``occurredAt`` and optionally
        ``eventId``, ``actionSource``, ``sourceUrl``, ``email``, ``phone``, ``externalId``,
        ``clientIpAddress``, ``clientUserAgent``, ``clickId``, ``browserId``, ``contentIds``,
        ``valueMinor``, ``currency``, ``orderId``.
        """
        return self._send_conversions(
            "/ads/conversions",
            workspace_id,
            connection_id,
            ad_account_id,
            pixel_id,
            events,
            idempotency_key,
        )

    def send_conversions(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        pixel_id: str,
        events: Sequence[Mapping[str, Any]],
        idempotency_key: str,
    ) -> ConversionUploadResult:
        """The Conversions API send. ``idempotency_key`` is required: a reused key
        answers ``replayed=True`` and nothing reaches the network again."""
        return self._send_conversions(
            "/ads/conversions/events",
            workspace_id,
            connection_id,
            ad_account_id,
            pixel_id,
            events,
            idempotency_key,
        )

    def _send_conversions(
        self,
        path: str,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        pixel_id: str,
        events: Sequence[Mapping[str, Any]],
        idempotency_key: str | None,
    ) -> ConversionUploadResult:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return ConversionUploadResult.model_validate(
            unwrap(
                self._http.post(
                    path,
                    {
                        "workspaceId": workspace_id,
                        "connectionId": connection_id,
                        "adAccountId": ad_account_id,
                        "pixelId": pixel_id,
                        "events": [dict(e) for e in events],
                    },
                    headers=headers,
                )
            )
        )

    def conversion_batches(
        self,
        *,
        workspace_id: str | None = None,
        connection_id: str | None = None,
        limit: int | None = None,
    ) -> builtins.list[ConversionBatch]:
        """Stored batches, newest first, with hashed identifiers only."""
        return parse_list(
            ConversionBatch,
            unwrap(
                self._http.get(
                    "/ads/conversions/events",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "limit": limit,
                    },
                )
            ),
        )

    # ─── Pixels, match quality and custom conversions ───────────────────

    def pixels(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[AdPixel]:
        return parse_list(
            AdPixel,
            unwrap(
                self._http.get(
                    "/ads/pixels", self._account_params(workspace_id, connection_id, ad_account_id)
                )
            ),
        )

    def create_pixel(
        self, *, workspace_id: str, connection_id: str, ad_account_id: str, name: str
    ) -> AdPixelDetail:
        """``code`` on the answer is the script to place on the site."""
        return AdPixelDetail.model_validate(
            unwrap(
                self._http.post(
                    "/ads/pixels",
                    {
                        "workspaceId": workspace_id,
                        "connectionId": connection_id,
                        "adAccountId": ad_account_id,
                        "name": name,
                    },
                )
            )
        )

    def get_pixel(
        self,
        pixel_id: str,
        *,
        connection_id: str,
        ad_account_id: str,
        workspace_id: str | None = None,
    ) -> AdPixelDetail:
        return AdPixelDetail.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/pixels/{pixel_id}",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            )
        )

    def update_pixel(
        self,
        pixel_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str | None = None,
        data_use_setting: str | None = None,
    ) -> AdPixelDetail:
        """``data_use_setting`` is one of ``PIXEL_DATA_USE_SETTINGS``."""
        body = drop_unset(
            {
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adAccountId": ad_account_id,
                "name": name if name is not None else UNSET,
                "dataUseSetting": data_use_setting if data_use_setting is not None else UNSET,
            }
        )
        return AdPixelDetail.model_validate(
            unwrap(self._http.patch(f"/ads/pixels/{pixel_id}", body))
        )

    def share_pixel(
        self,
        pixel_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        target_ad_account_id: str,
    ) -> None:
        """Share the pixel with another ad account under the same business portfolio."""
        self._http.post(
            f"/ads/pixels/{pixel_id}/share",
            {
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adAccountId": ad_account_id,
                "targetAdAccountId": target_ad_account_id,
            },
        )

    def pixel_stats(
        self,
        pixel_id: str,
        *,
        connection_id: str,
        ad_account_id: str,
        workspace_id: str | None = None,
    ) -> PixelStats:
        return PixelStats.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/pixels/{pixel_id}/stats",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            )
        )

    def event_match_quality(
        self,
        pixel_id: str,
        *,
        connection_id: str,
        ad_account_id: str,
        workspace_id: str | None = None,
    ) -> builtins.list[EventMatchQuality]:
        return parse_list(
            EventMatchQuality,
            unwrap(
                self._http.get(
                    f"/ads/pixels/{pixel_id}/match-quality",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            ),
        )

    def custom_conversions(
        self, *, connection_id: str, ad_account_id: str, workspace_id: str | None = None
    ) -> builtins.list[CustomConversion]:
        return parse_list(
            CustomConversion,
            unwrap(
                self._http.get(
                    "/ads/custom-conversions",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            ),
        )

    def create_custom_conversion(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        pixel_id: str,
        name: str,
        event_type: str,
        rule: Mapping[str, Any],
        description: str | None = None,
        default_value_minor: int | None = None,
    ) -> CustomConversion:
        """``event_type`` is one of ``CUSTOM_CONVERSION_EVENT_TYPES``; ``rule`` carries
        ``eventName`` and one of ``urlContains`` or ``urlEquals``."""
        body = drop_unset(
            {
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adAccountId": ad_account_id,
                "pixelId": pixel_id,
                "name": name,
                "eventType": event_type,
                "rule": dict(rule),
                "description": description if description is not None else UNSET,
                "defaultValueMinor": default_value_minor
                if default_value_minor is not None
                else UNSET,
            }
        )
        return CustomConversion.model_validate(
            unwrap(self._http.post("/ads/custom-conversions", body))
        )

    def get_custom_conversion(
        self,
        conversion_id: str,
        *,
        connection_id: str,
        ad_account_id: str,
        workspace_id: str | None = None,
    ) -> CustomConversion:
        return CustomConversion.model_validate(
            unwrap(
                self._http.get(
                    f"/ads/custom-conversions/{conversion_id}",
                    self._account_params(workspace_id, connection_id, ad_account_id),
                )
            )
        )

    def update_custom_conversion(
        self,
        conversion_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        ad_account_id: str,
        name: str | None = None,
        description: str | None = None,
        default_value_minor: int | None = None,
    ) -> CustomConversion:
        body = drop_unset(
            {
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adAccountId": ad_account_id,
                "name": name if name is not None else UNSET,
                "description": description if description is not None else UNSET,
                "defaultValueMinor": default_value_minor
                if default_value_minor is not None
                else UNSET,
            }
        )
        return CustomConversion.model_validate(
            unwrap(self._http.patch(f"/ads/custom-conversions/{conversion_id}", body))
        )

    def delete_custom_conversion(
        self, conversion_id: str, *, workspace_id: str, connection_id: str, ad_account_id: str
    ) -> None:
        self._http.delete(
            f"/ads/custom-conversions/{conversion_id}",
            {
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adAccountId": ad_account_id,
            },
        )

    def comments(
        self,
        *,
        connection_id: str,
        ad_id: str,
        after: str | None = None,
        workspace_id: str | None = None,
    ) -> AdCommentsPage:
        """One page of an ad's comments; pass ``next_cursor`` back as ``after``."""
        return AdCommentsPage.model_validate(
            unwrap(
                self._http.get(
                    "/ads/comments",
                    {
                        "workspace_id": workspace_id,
                        "connection_id": connection_id,
                        "ad_id": ad_id,
                        "after": after,
                    },
                )
            )
        )

    def reply_to_comment(
        self, comment_id: str, *, workspace_id: str, connection_id: str, ad_id: str, text: str
    ) -> dict[str, Any]:
        """Needs the ``publish`` scope as well as ``ads``."""
        result = unwrap(
            self._http.post(
                f"/ads/comments/{comment_id}/reply",
                {
                    "workspaceId": workspace_id,
                    "connectionId": connection_id,
                    "adId": ad_id,
                    "text": text,
                },
            )
        )
        return result if isinstance(result, dict) else {"data": result}

    def set_comment_hidden(
        self, comment_id: str, *, workspace_id: str, connection_id: str, ad_id: str, hidden: bool
    ) -> None:
        """Needs the ``publish`` scope as well as ``ads``."""
        self._http.post(
            f"/ads/comments/{comment_id}/hide",
            {
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adId": ad_id,
                "hidden": hidden,
            },
        )

    def delete_comment(
        self, comment_id: str, *, workspace_id: str, connection_id: str, ad_id: str
    ) -> None:
        """One already gone on the network succeeds. Needs ``publish`` as well as ``ads``."""
        self._http.request(
            "DELETE",
            f"/ads/comments/{comment_id}",
            json={
                "workspaceId": workspace_id,
                "connectionId": connection_id,
                "adId": ad_id,
            },
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

    def _rule(
        self,
        method: str,
        rule_id: str,
        suffix: str,
        workspace_id: str | None,
        connection_id: str,
        body: Mapping[str, Any] | None = None,
    ) -> Any:
        return self._http.request(
            method,
            f"/ads/linkedin/conversion-rules/{rule_id}{suffix}",
            json=dict(body) if body is not None else None,
            params={"workspace_id": workspace_id, "connection_id": connection_id},
        )
