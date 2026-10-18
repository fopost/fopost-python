"""``client.webhook_endpoints`` — the HTTPS endpoints FoPost delivers events to.

Named apart from :mod:`fopost.webhooks`, which verifies the deliveries these
endpoints receive.
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import WebhookDelivery, WebhookEndpoint
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["WebhookEndpointsResource"]


class WebhookEndpointsResource(Resource):
    def list(self) -> builtins.list[WebhookEndpoint]:
        return parse_list(WebhookEndpoint, unwrap(self._http.get("/webhooks")))

    def create(
        self,
        *,
        workspace_id: str,
        url: str,
        events: Sequence[str],
        name: str | None = None,
        secret: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> WebhookEndpoint:
        """Register an endpoint. The signing ``secret`` comes back only here."""
        body: dict[str, Any] = {"workspaceId": workspace_id, "url": url, "events": list(events)}
        optional = {
            "name": name,
            "secret": secret,
            "headers": dict(headers) if headers is not None else None,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return WebhookEndpoint.model_validate(unwrap(self._http.post("/webhooks", body)))

    def update(
        self,
        webhook_id: str,
        *,
        name: str | None | Any = UNSET,
        url: str | Any = UNSET,
        events: Sequence[str] | Any = UNSET,
        active: bool | Any = UNSET,
        secret: str | Any = UNSET,
        headers: Mapping[str, str] | None | Any = UNSET,
    ) -> WebhookEndpoint:
        """Partial update. ``active=True`` on a paused webhook resets its failure count."""
        body = drop_unset(
            {
                "name": name,
                "url": url,
                "events": list(events) if events is not UNSET else UNSET,
                "active": active,
                "secret": secret,
                "headers": dict(headers) if isinstance(headers, Mapping) else headers,
            }
        )
        return WebhookEndpoint.model_validate(
            unwrap(self._http.put(f"/webhooks/{webhook_id}", body))
        )

    def delete(self, webhook_id: str) -> None:
        self._http.delete(f"/webhooks/{webhook_id}")

    def test(self, webhook_id: str) -> None:
        """Dispatch a test ``post.published`` payload to this endpoint only."""
        self._http.post(f"/webhooks/{webhook_id}/test")

    def deliveries(
        self, webhook_id: str, *, status: str | None = None, limit: int | None = None
    ) -> builtins.list[WebhookDelivery]:
        """Attempts from the last 30 days, newest first. ``status`` is ``success`` or ``failed``."""
        return parse_list(
            WebhookDelivery,
            unwrap(
                self._http.get(
                    f"/webhooks/{webhook_id}/deliveries", {"status": status, "limit": limit}
                )
            ),
        )

    def get_delivery(self, webhook_id: str, delivery_id: str) -> WebhookDelivery:
        """One attempt, including the payload that was sent."""
        return WebhookDelivery.model_validate(
            unwrap(self._http.get(f"/webhooks/{webhook_id}/deliveries/{delivery_id}"))
        )

    def redeliver(self, webhook_id: str, delivery_id: str) -> None:
        """Send the identical body again, logged as the next attempt. A paused webhook is 409."""
        self._http.post(f"/webhooks/{webhook_id}/deliveries/{delivery_id}/redeliver")
