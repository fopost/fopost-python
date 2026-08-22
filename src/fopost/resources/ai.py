"""``client.ai`` — caption assist, per-platform rewriting, and blog fan-out.

Every call spends AI credits. Check the balance with :meth:`AiResource.credits`;
a ``PaymentRequiredError`` means the plan has none left.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._http import unwrap
from ..models import AiCreditBalance, CaptionResult, RepurposeResult, RewriteResult
from ._base import Resource

__all__ = ["AiResource"]


class AiResource(Resource):
    def credits(self) -> AiCreditBalance:
        """Credits remaining, used, and total for the current billing period."""
        return AiCreditBalance.model_validate(unwrap(self._http.get("/ai/credits")))

    def generate_caption(
        self,
        *,
        current_caption: str | None = None,
        image_urls: Sequence[str] | None = None,
        platforms: Sequence[str] | None = None,
        char_limit: int | None = None,
        workspace_id: str | None = None,
        brand_voice_id: str | None = None,
    ) -> CaptionResult:
        body: dict[str, Any] = {
            "current_caption": current_caption,
            "image_urls": list(image_urls) if image_urls is not None else None,
            "platforms": list(platforms) if platforms is not None else None,
            "char_limit": char_limit,
            "workspace_id": workspace_id,
            "brand_voice_id": brand_voice_id,
        }
        return CaptionResult.model_validate(
            unwrap(self._http.post("/ai/generate-caption", _compact(body)))
        )

    def rewrite(
        self,
        *,
        content: str,
        platforms: Sequence[str],
        tone: str | None = None,
        workspace_id: str | None = None,
        brand_voice_id: str | None = None,
    ) -> RewriteResult:
        """Rewrite one draft for each target platform. Costs 1 credit per platform."""
        body: dict[str, Any] = {
            "content": content,
            "platforms": list(platforms),
            "tone": tone,
            "workspace_id": workspace_id,
            "brand_voice_id": brand_voice_id,
        }
        return RewriteResult.model_validate(unwrap(self._http.post("/ai/rewrite", _compact(body))))

    def repurpose_url(
        self,
        *,
        url: str,
        platforms: Sequence[str],
        workspace_id: str | None = None,
        brand_voice_id: str | None = None,
    ) -> RepurposeResult:
        """Turn an article URL into a post for each platform, in one call."""
        body: dict[str, Any] = {
            "url": url,
            "platforms": list(platforms),
            "workspace_id": workspace_id,
            "brand_voice_id": brand_voice_id,
        }
        return RepurposeResult.model_validate(
            unwrap(self._http.post("/ai/repurpose-url", _compact(body)))
        )


def _compact(body: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in body.items() if v is not None}
