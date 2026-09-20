"""``client.google_business`` — manage a connected Google Business Profile location.

Google grants Business Profile API access per project. Until that grant lands
on a deployment every call here raises a 503 ``configuration_error``.

Responses relay Google's own shape, field for field, so a field you know from
the Business Profile APIs is the field you get back; they come through as
plain dicts rather than models we would have to keep chasing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import AccountMove
from ._base import UNSET, Resource, drop_unset

__all__ = ["GoogleBusinessResource"]

Payload = dict[str, Any]

#: The set fetched when a caller names no metrics.
DEFAULT_DAILY_METRICS = (
    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
    "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
    "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
    "CALL_CLICKS",
    "WEBSITE_CLICKS",
    "BUSINESS_DIRECTION_REQUESTS",
)


def _payload(data: Any) -> Payload:
    return data if isinstance(data, dict) else {"data": data}


class GoogleBusinessResource(Resource):
    # ── Location ──────────────────────────────────────────────────

    def get_location(self, account_id: str) -> Payload:
        return _payload(unwrap(self._http.get(f"/accounts/{account_id}/gbp/location")))

    def update_location(
        self,
        account_id: str,
        *,
        title: str | Any = UNSET,
        description: str | None | Any = UNSET,
        website_uri: str | None | Any = UNSET,
        primary_phone: str | None | Any = UNSET,
        additional_phones: Sequence[str] | Any = UNSET,
        store_code: str | None | Any = UNSET,
        regular_hours: Sequence[Mapping[str, Any]] | Any = UNSET,
    ) -> Payload:
        """Patch the profile; an argument left out keeps its value."""
        body = drop_unset(
            {
                "title": title,
                "description": description,
                "website_uri": website_uri,
                "primary_phone": primary_phone,
                "additional_phones": additional_phones,
                "store_code": store_code,
                "regular_hours": regular_hours,
            }
        )
        return _payload(
            unwrap(self._http.request("PATCH", f"/accounts/{account_id}/gbp/location", json=body))
        )

    # ── Attributes ────────────────────────────────────────────────

    def get_attributes(
        self,
        account_id: str,
        *,
        available: bool | None = None,
        category_name: str | None = None,
        region_code: str | None = None,
        language_code: str | None = None,
    ) -> Payload:
        """The values set on the location, or what Google offers it."""
        return _payload(
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/gbp/attributes",
                    {
                        "available": available,
                        "category_name": category_name,
                        "region_code": region_code,
                        "language_code": language_code,
                    },
                )
            )
        )

    def update_attributes(
        self, account_id: str, attributes: Sequence[Mapping[str, Any]]
    ) -> Payload:
        """Only the named attributes change; every other one is left alone."""
        return _payload(
            unwrap(
                self._http.request(
                    "PATCH",
                    f"/accounts/{account_id}/gbp/attributes",
                    json={"attributes": list(attributes)},
                )
            )
        )

    # ── Food menus and services ───────────────────────────────────

    def get_menus(self, account_id: str) -> Payload:
        return _payload(unwrap(self._http.get(f"/accounts/{account_id}/gbp/menus")))

    def replace_menus(self, account_id: str, menus: Sequence[Mapping[str, Any]]) -> Payload:
        """Google has no per-section patch, so the whole menu set is replaced."""
        return _payload(
            unwrap(self._http.put(f"/accounts/{account_id}/gbp/menus", {"menus": list(menus)}))
        )

    def get_services(self, account_id: str) -> Payload:
        return _payload(unwrap(self._http.get(f"/accounts/{account_id}/gbp/services")))

    def replace_services(
        self, account_id: str, service_items: Sequence[Mapping[str, Any]]
    ) -> Payload:
        return _payload(
            unwrap(
                self._http.put(
                    f"/accounts/{account_id}/gbp/services",
                    {"service_items": list(service_items)},
                )
            )
        )

    # ── Photos ────────────────────────────────────────────────────

    def list_media(
        self, account_id: str, *, page_size: int | None = None, page_token: str | None = None
    ) -> Payload:
        return _payload(
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/gbp/media",
                    {"page_size": page_size, "page_token": page_token},
                )
            )
        )

    def add_media(
        self,
        account_id: str,
        *,
        media_id: str,
        category: str = "ADDITIONAL",
        description: str | None = None,
    ) -> Payload:
        """The photo is a media-library asset in the same workspace, JPEG or PNG."""
        body: Payload = {"media_id": media_id, "category": category}
        if description is not None:
            body["description"] = description
        return _payload(unwrap(self._http.post(f"/accounts/{account_id}/gbp/media", body)))

    def delete_media(self, account_id: str, media_key: str) -> Payload:
        return _payload(unwrap(self._http.delete(f"/accounts/{account_id}/gbp/media/{media_key}")))

    # ── Place action links ────────────────────────────────────────

    def list_place_actions(self, account_id: str) -> Payload:
        return _payload(unwrap(self._http.get(f"/accounts/{account_id}/gbp/place-actions")))

    def create_place_action(
        self,
        account_id: str,
        *,
        uri: str,
        place_action_type: str,
        is_preferred: bool | None = None,
    ) -> Payload:
        body: Payload = {"uri": uri, "place_action_type": place_action_type}
        if is_preferred is not None:
            body["is_preferred"] = is_preferred
        return _payload(unwrap(self._http.post(f"/accounts/{account_id}/gbp/place-actions", body)))

    def update_place_action(
        self,
        account_id: str,
        link_id: str,
        *,
        uri: str | Any = UNSET,
        is_preferred: bool | Any = UNSET,
    ) -> Payload:
        body = drop_unset({"uri": uri, "is_preferred": is_preferred})
        return _payload(
            unwrap(
                self._http.request(
                    "PATCH", f"/accounts/{account_id}/gbp/place-actions/{link_id}", json=body
                )
            )
        )

    def delete_place_action(self, account_id: str, link_id: str) -> Payload:
        return _payload(
            unwrap(self._http.delete(f"/accounts/{account_id}/gbp/place-actions/{link_id}"))
        )

    # ── Verification ──────────────────────────────────────────────

    def get_verification_options(
        self, account_id: str, *, language_code: str | None = None
    ) -> Payload:
        """The ways Google will let this location be verified."""
        return _payload(
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/gbp/verification", {"language_code": language_code}
                )
            )
        )

    def start_verification(
        self,
        account_id: str,
        *,
        method: str,
        language_code: str | None = None,
        phone_number: str | None = None,
        email_address: str | None = None,
        mailer_contact_name: str | None = None,
    ) -> Payload:
        """The response names the pending verification to complete with the PIN."""
        body: Payload = {"method": method}
        for key, value in (
            ("language_code", language_code),
            ("phone_number", phone_number),
            ("email_address", email_address),
            ("mailer_contact_name", mailer_contact_name),
        ):
            if value is not None:
                body[key] = value
        return _payload(
            unwrap(self._http.post(f"/accounts/{account_id}/gbp/verification/start", body))
        )

    def complete_verification(
        self, account_id: str, *, verification_name: str, pin: str
    ) -> Payload:
        return _payload(
            unwrap(
                self._http.post(
                    f"/accounts/{account_id}/gbp/verification/complete",
                    {"verification_name": verification_name, "pin": pin},
                )
            )
        )

    # ── Performance ───────────────────────────────────────────────

    def get_performance(
        self,
        account_id: str,
        *,
        start_date: str,
        end_date: str,
        daily_metrics: Sequence[str] | None = None,
    ) -> Payload:
        """Daily impressions, calls, direction requests and clicks for the range."""
        return _payload(
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/gbp/performance",
                    {
                        "start_date": start_date,
                        "end_date": end_date,
                        "daily_metrics": list(daily_metrics) if daily_metrics else None,
                    },
                )
            )
        )

    def get_search_keywords(
        self, account_id: str, *, start_date: str, end_date: str, page_token: str | None = None
    ) -> Payload:
        """The search terms people used to find the listing, by month."""
        return _payload(
            unwrap(
                self._http.get(
                    f"/accounts/{account_id}/gbp/performance",
                    {
                        "keywords": True,
                        "start_date": start_date,
                        "end_date": end_date,
                        "page_token": page_token,
                    },
                )
            )
        )

    # ── Workspace assignment ──────────────────────────────────────

    def assign(self, account_id: str, *, workspace_id: str) -> AccountMove:
        """Hand the location to another workspace; the caller must own both."""
        return AccountMove.model_validate(
            unwrap(
                self._http.post(
                    f"/accounts/{account_id}/gbp/assign", {"workspace_id": workspace_id}
                )
            )
        )
