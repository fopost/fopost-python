"""``client.ads.google`` — the Google Ads surface no other network has.

Campaigns, ad groups, ads, audiences and insights live on ``client.ads`` and
dispatch by connection. What is here — keywords, assets, Performance Max asset
groups, Local Services leads, conversions and raw GAQL — is Google only, and a
connection on another network answers 400.

Every method needs the ``ads`` scope; anything that changes what a live account
serves or bids also needs ``publish``. ``customer_id`` is digits only and has
to name an account the connection's grant reaches: any other answers 404.
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    GoogleAdScheduleSlot,
    GoogleAssetGroup,
    GoogleAssetsResult,
    GoogleBidStrategy,
    GoogleConversionAction,
    GoogleKeyword,
    GoogleKeywordIdea,
    GoogleLocalServicesLead,
    GoogleSearchTerm,
    GoogleSharedSet,
)
from ._base import Resource, parse_list

__all__ = ["GoogleAdsResource"]


class GoogleAdsResource(Resource):
    # ── Keywords ──

    def keywords(
        self,
        *,
        connection_id: str,
        customer_id: str,
        workspace_id: str | None = None,
        ad_group_id: str | None = None,
    ) -> builtins.list[GoogleKeyword]:
        """Keywords on the account, or on one ad group."""
        return parse_list(
            GoogleKeyword,
            unwrap(
                self._http.get(
                    "/ads/google/keywords",
                    _query(workspace_id, connection_id, customer_id, ad_group_id=ad_group_id),
                )
            ),
        )

    def create_keyword(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        ad_group_id: str,
        text: str,
        match_type: str,
        cpc_bid_minor: int | None = None,
    ) -> str:
        """The new keyword's id. Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["adGroupId"] = ad_group_id
        body["text"] = text
        body["matchType"] = match_type
        if cpc_bid_minor is not None:
            body["cpcBidMinor"] = cpc_bid_minor
        return _id(unwrap(self._http.post("/ads/google/keywords", body)))

    def update_keyword(
        self,
        keyword_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        status: str | None = None,
        cpc_bid_minor: int | None = None,
    ) -> str:
        """``status`` is ``active`` or ``paused``. Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        if status is not None:
            body["status"] = status
        if cpc_bid_minor is not None:
            body["cpcBidMinor"] = cpc_bid_minor
        return _id(
            unwrap(self._http.request("PATCH", f"/ads/google/keywords/{keyword_id}", json=body))
        )

    def delete_keyword(
        self, keyword_id: str, *, workspace_id: str, connection_id: str, customer_id: str
    ) -> None:
        """Needs ``publish`` as well as ``ads``."""
        self._http.delete(
            f"/ads/google/keywords/{keyword_id}",
            json=_scope(workspace_id, connection_id, customer_id),
        )

    def keyword_ideas(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        seeds: Sequence[str] | None = None,
        url: str | None = None,
        language_id: str | None = None,
        geo_target_ids: Sequence[str] | None = None,
    ) -> builtins.list[GoogleKeywordIdea]:
        """Ideas from seed keywords, a landing page, or both."""
        body = _scope(workspace_id, connection_id, customer_id)
        if seeds is not None:
            body["seeds"] = list(seeds)
        if url is not None:
            body["url"] = url
        if language_id is not None:
            body["languageId"] = language_id
        if geo_target_ids is not None:
            body["geoTargetIds"] = list(geo_target_ids)
        return parse_list(
            GoogleKeywordIdea, unwrap(self._http.post("/ads/google/keyword-ideas", body))
        )

    def keyword_metrics(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        keywords: Sequence[str],
    ) -> builtins.list[GoogleKeywordIdea]:
        body = _scope(workspace_id, connection_id, customer_id)
        body["keywords"] = list(keywords)
        return parse_list(
            GoogleKeywordIdea, unwrap(self._http.post("/ads/google/keyword-metrics", body))
        )

    def search_terms(
        self,
        *,
        connection_id: str,
        customer_id: str,
        since: str,
        until: str,
        workspace_id: str | None = None,
    ) -> builtins.list[GoogleSearchTerm]:
        """What people actually searched, with the metrics each term earned."""
        return parse_list(
            GoogleSearchTerm,
            unwrap(
                self._http.get(
                    "/ads/google/search-terms",
                    _query(workspace_id, connection_id, customer_id, since=since, until=until),
                )
            ),
        )

    # ── Bid strategies and ad schedule ──

    def bid_strategies(
        self, *, connection_id: str, customer_id: str, workspace_id: str | None = None
    ) -> builtins.list[GoogleBidStrategy]:
        return parse_list(
            GoogleBidStrategy,
            unwrap(
                self._http.get(
                    "/ads/google/bid-strategies", _query(workspace_id, connection_id, customer_id)
                )
            ),
        )

    def create_bid_strategy(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        name: str,
        type: str,
        target_minor: int | None = None,
    ) -> str:
        """Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["name"] = name
        body["type"] = type
        if target_minor is not None:
            body["targetMinor"] = target_minor
        return _id(unwrap(self._http.post("/ads/google/bid-strategies", body)))

    def ad_schedule(
        self,
        *,
        connection_id: str,
        customer_id: str,
        campaign_id: str,
        workspace_id: str | None = None,
    ) -> builtins.list[GoogleAdScheduleSlot]:
        return parse_list(
            GoogleAdScheduleSlot,
            unwrap(
                self._http.get(
                    "/ads/google/ad-schedule",
                    _query(workspace_id, connection_id, customer_id, campaign_id=campaign_id),
                )
            ),
        )

    def set_ad_schedule(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        campaign_id: str,
        slots: Sequence[Mapping[str, Any]],
    ) -> int:
        """Replaces every slot on the campaign. Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["campaignId"] = campaign_id
        body["slots"] = [dict(slot) for slot in slots]
        result = unwrap(self._http.put("/ads/google/ad-schedule", body))
        return int(result.get("slots", 0)) if isinstance(result, dict) else 0

    # ── Negative keyword lists ──

    def negative_keyword_lists(
        self, *, connection_id: str, customer_id: str, workspace_id: str | None = None
    ) -> builtins.list[GoogleSharedSet]:
        return parse_list(
            GoogleSharedSet,
            unwrap(
                self._http.get(
                    "/ads/google/negative-keywords",
                    _query(workspace_id, connection_id, customer_id),
                )
            ),
        )

    def create_negative_keyword_list(
        self, *, workspace_id: str, connection_id: str, customer_id: str, name: str
    ) -> str:
        """Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["name"] = name
        return _id(unwrap(self._http.post("/ads/google/negative-keywords", body)))

    def add_negative_keywords(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        shared_set_id: str,
        keywords: Sequence[Mapping[str, Any]],
    ) -> int:
        """How many were added. Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["sharedSetId"] = shared_set_id
        body["keywords"] = [dict(keyword) for keyword in keywords]
        result = unwrap(self._http.post("/ads/google/negative-keywords/keywords", body))
        return int(result.get("added", 0)) if isinstance(result, dict) else 0

    def attach_negative_keyword_list(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        shared_set_id: str,
        campaign_id: str,
    ) -> None:
        """Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["sharedSetId"] = shared_set_id
        body["campaignId"] = campaign_id
        self._http.post("/ads/google/negative-keywords/attach", body)

    # ── Assets ──

    def assets(
        self, *, connection_id: str, customer_id: str, workspace_id: str | None = None
    ) -> GoogleAssetsResult:
        """Sitelinks, callouts and snippets, with the links that put each under an ad."""
        data = unwrap(
            self._http.get("/ads/google/assets", _query(workspace_id, connection_id, customer_id))
        )
        return GoogleAssetsResult.model_validate(data if isinstance(data, dict) else {})

    def create_asset(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        spec: Mapping[str, Any],
    ) -> str:
        """``spec`` is a sitelink, callout or snippet. Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["spec"] = dict(spec)
        return _id(unwrap(self._http.post("/ads/google/assets", body)))

    def attach_asset(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        asset_id: str,
        field_type: str,
        campaign_id: str | None = None,
    ) -> None:
        """Attaches to the account when ``campaign_id`` is left out. Needs ``publish``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["assetId"] = asset_id
        body["fieldType"] = field_type
        if campaign_id is not None:
            body["campaignId"] = campaign_id
        self._http.post("/ads/google/assets/attach", body)

    def delete_asset(
        self, asset_id: str, *, workspace_id: str, connection_id: str, customer_id: str
    ) -> None:
        """Removes the links that put it under an ad; on Google the asset itself is permanent."""
        self._http.delete(
            f"/ads/google/assets/{asset_id}",
            json=_scope(workspace_id, connection_id, customer_id),
        )

    # ── Performance Max asset groups ──

    def asset_groups(
        self,
        *,
        connection_id: str,
        customer_id: str,
        workspace_id: str | None = None,
        campaign_id: str | None = None,
    ) -> builtins.list[GoogleAssetGroup]:
        return parse_list(
            GoogleAssetGroup,
            unwrap(
                self._http.get(
                    "/ads/google/asset-groups",
                    _query(workspace_id, connection_id, customer_id, campaign_id=campaign_id),
                )
            ),
        )

    def create_asset_group(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        campaign_id: str,
        name: str,
        final_urls: Sequence[str],
        status: str | None = None,
    ) -> str:
        """Starts paused unless ``status`` says otherwise. Needs ``publish``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["campaignId"] = campaign_id
        body["name"] = name
        body["finalUrls"] = list(final_urls)
        if status is not None:
            body["status"] = status
        return _id(unwrap(self._http.post("/ads/google/asset-groups", body)))

    def update_asset_group(
        self,
        asset_group_id: str,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        name: str | None = None,
        status: str | None = None,
    ) -> str:
        """Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        if name is not None:
            body["name"] = name
        if status is not None:
            body["status"] = status
        return _id(
            unwrap(
                self._http.request("PATCH", f"/ads/google/asset-groups/{asset_group_id}", json=body)
            )
        )

    def delete_asset_group(
        self, asset_group_id: str, *, workspace_id: str, connection_id: str, customer_id: str
    ) -> None:
        """Needs ``publish`` as well as ``ads``."""
        self._http.delete(
            f"/ads/google/asset-groups/{asset_group_id}",
            json=_scope(workspace_id, connection_id, customer_id),
        )

    # ── Local Services leads ──

    def local_services_leads(
        self,
        *,
        connection_id: str,
        customer_id: str,
        since: str,
        until: str,
        workspace_id: str | None = None,
    ) -> builtins.list[GoogleLocalServicesLead]:
        """Read live on every call and never stored by FoPost."""
        return parse_list(
            GoogleLocalServicesLead,
            unwrap(
                self._http.get(
                    "/ads/google/local-services",
                    _query(workspace_id, connection_id, customer_id, since=since, until=until),
                )
            ),
        )

    # ── Conversions ──

    def conversion_actions(
        self, *, connection_id: str, customer_id: str, workspace_id: str | None = None
    ) -> builtins.list[GoogleConversionAction]:
        return parse_list(
            GoogleConversionAction,
            unwrap(
                self._http.get(
                    "/ads/google/conversions", _query(workspace_id, connection_id, customer_id)
                )
            ),
        )

    def create_conversion_action(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        name: str,
        category: str,
        value_minor: int | None = None,
        counting_type: str | None = None,
    ) -> str:
        """Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["name"] = name
        body["category"] = category
        if value_minor is not None:
            body["valueMinor"] = value_minor
        if counting_type is not None:
            body["countingType"] = counting_type
        return _id(unwrap(self._http.post("/ads/google/conversions", body)))

    def upload_conversions(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        conversions: Sequence[Mapping[str, Any]],
    ) -> int:
        """Offline conversions, matched to a click. Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["conversions"] = [dict(conversion) for conversion in conversions]
        result = unwrap(self._http.post("/ads/google/conversions/upload", body))
        return int(result.get("uploaded", 0)) if isinstance(result, dict) else 0

    def upload_conversion_adjustments(
        self,
        *,
        workspace_id: str,
        connection_id: str,
        customer_id: str,
        adjustments: Sequence[Mapping[str, Any]],
    ) -> int:
        """Needs ``publish`` as well as ``ads``."""
        body = _scope(workspace_id, connection_id, customer_id)
        body["adjustments"] = [dict(adjustment) for adjustment in adjustments]
        result = unwrap(self._http.post("/ads/google/conversions/adjustments", body))
        return int(result.get("uploaded", 0)) if isinstance(result, dict) else 0

    # ── GAQL ──

    def query(
        self,
        *,
        connection_id: str,
        customer_id: str,
        query: str,
        workspace_id: str | None = None,
    ) -> builtins.list[dict[str, Any]]:
        """A read-only GAQL SELECT; rows come back exactly as Google returns them."""
        body: dict[str, Any] = {
            "connectionId": connection_id,
            "customerId": customer_id,
            "query": query,
        }
        if workspace_id is not None:
            body["workspaceId"] = workspace_id
        result = unwrap(self._http.post("/ads/insights/query", body))
        rows = result.get("rows") if isinstance(result, dict) else None
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _scope(workspace_id: str, connection_id: str, customer_id: str) -> dict[str, Any]:
    return {
        "workspaceId": workspace_id,
        "connectionId": connection_id,
        "customerId": customer_id,
    }


def _query(
    workspace_id: str | None, connection_id: str, customer_id: str, **extra: Any
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "workspace_id": workspace_id,
        "connection_id": connection_id,
        "customer_id": customer_id,
    }
    params.update(extra)
    return params


def _id(result: Any) -> str:
    value = result.get("id") if isinstance(result, dict) else None
    return str(value) if value else ""
