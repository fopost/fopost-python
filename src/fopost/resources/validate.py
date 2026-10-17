"""``client.validate`` — the preflight checks for content that is not a post yet.

Nothing is stored. Every call needs the ``posts`` scope.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    SubredditCheck,
    ValidateLengthResult,
    ValidateMediaResult,
    ValidatePostResult,
)
from ._base import Resource

__all__ = ["ValidateResource"]


class ValidateResource(Resource):
    def post(
        self,
        *,
        platforms: Sequence[str],
        content: str | None = None,
        media: Sequence[dict[str, Any]] | None = None,
    ) -> ValidatePostResult:
        """Issues and advisory signals per platform, as preflight would answer.

        Each ``media`` item is ``{"url": ..., "mime_type": ..., "size": ...}``.
        """
        body: dict[str, Any] = {"platforms": list(platforms)}
        if content is not None:
            body["content"] = content
        if media is not None:
            body["media"] = list(media)
        return ValidatePostResult.model_validate(unwrap(self._http.post("/validate/post", body)))

    def length(self, *, text: str, platforms: Sequence[str]) -> ValidateLengthResult:
        """Counted length against each platform's limit."""
        body = {"text": text, "platforms": list(platforms)}
        return ValidateLengthResult.model_validate(
            unwrap(self._http.post("/validate/length", body))
        )

    def media(self, *, url: str) -> ValidateMediaResult:
        """Fetches the file and runs the upload checks on it; nothing is stored."""
        return ValidateMediaResult.model_validate(
            unwrap(self._http.post("/validate/media", {"url": url}))
        )

    def subreddit(self, *, account_id: str, name: str) -> SubredditCheck:
        """Whether a subreddit exists and takes a post from this Reddit account.

        The check runs with the account's own token, so ``account_id`` is required.
        """
        return SubredditCheck.model_validate(
            unwrap(self._http.get("/validate/subreddit", {"account_id": account_id, "name": name}))
        )
