"""The ``Fopost`` client."""

from __future__ import annotations

import os
from types import TracebackType
from typing import Any

import httpx

from ._http import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, HttpClient
from .resources import (
    AccountsResource,
    AiResource,
    LabelsResource,
    PostsResource,
    WorkspacesResource,
)

__all__ = ["Fopost"]


class Fopost:
    """Client for the FoPost API.

    ::

        from fopost import Fopost

        client = Fopost(api_key="osk_...")
        accounts = client.accounts.list(workspace_id="9b2f6c1e-...")

    The key falls back to the ``FOPOST_API_KEY`` environment variable.
    Requests that come back 429 are retried up to ``max_retries`` attempts,
    waiting for the interval the API asks for in ``Retry-After``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        key = api_key or os.environ.get("FOPOST_API_KEY")
        if not key:
            raise ValueError(
                "fopost: an api_key is required — pass api_key=... or set FOPOST_API_KEY"
            )

        self._http = HttpClient(
            api_key=key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            client=http_client,
        )

        self.posts = PostsResource(self._http)
        self.accounts = AccountsResource(self._http)
        self.workspaces = WorkspacesResource(self._http)
        self.labels = LabelsResource(self._http)
        self.ai = AiResource(self._http)

    @property
    def base_url(self) -> str:
        return self._http.base_url

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Call an endpoint the SDK does not wrap yet. Returns the decoded body."""
        return self._http.request(method, path, json=json, params=params)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Fopost:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
