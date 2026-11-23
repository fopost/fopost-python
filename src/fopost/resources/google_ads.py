"""``client.ads.google`` — the Google Ads surface no other network has.

Ads, audiences and insights live on ``client.ads`` and dispatch by connection.
What is here (bid strategies, the ad schedule, Local Services leads, conversions
and raw GAQL) is Google only, and a connection on another network answers 400.

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
    GoogleBidStrategy,
    GoogleConversionAction,
    GoogleLocalServicesLead,
)
from ._base import Resource, parse_list

__all__ = ["GoogleAdsResource"]


class GoogleAdsResource(Resource):
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
