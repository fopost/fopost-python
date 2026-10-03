"""Internal HTTP transport: auth headers, JSON coding, envelope unwrap, retries."""

from __future__ import annotations

import time
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

import httpx

from .errors import FopostError, RateLimitError, error_from_response

DEFAULT_BASE_URL = "https://api.fopost.com/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
MAX_RETRY_WAIT = 60.0

USER_AGENT = "fopost-python"

# Indirected so tests can replace the wait without touching the real clock.
_sleep = time.sleep


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """Parse Retry-After, which is either delta-seconds or an HTTP date."""
    raw = response.headers.get("retry-after")
    if not raw:
        return None
    raw = raw.strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    try:
        target = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if target is None:
        return None
    delta = target.timestamp() - time.time()
    return max(0.0, delta)


class HttpClient:
    """Thin httpx wrapper. One per ``Fopost`` instance."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("fopost: api_key is required")
        if max_retries < 1:
            raise ValueError("fopost: max_retries must be at least 1")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": USER_AGENT,
        }

    def _url(self, path: str) -> str:
        if urlsplit(path).scheme:
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send a request, retrying on 429, and return the decoded body."""
        clean_params = {k: v for k, v in params.items() if v is not None} if params else None

        attempt = 0
        while True:
            attempt += 1
            response = self._client.request(
                method,
                self._url(path),
                json=json,
                params=clean_params,
                headers=self.headers,
            )

            if response.status_code == 429 and attempt < self.max_retries:
                wait = _retry_after_seconds(response)
                _sleep(min(wait if wait is not None else 1.0, MAX_RETRY_WAIT))
                continue

            return self._decode(response)

    def _decode(self, response: httpx.Response) -> Any:
        body: Any
        if response.status_code == 204 or not response.content:
            body = None
        else:
            try:
                body = response.json()
            except ValueError:
                body = response.text

        if response.is_success:
            if isinstance(body, str):
                content_type = response.headers.get("content-type", "")
                raise FopostError(
                    f"Expected a JSON response, got {content_type or 'no content type'}",
                    status=response.status_code,
                    body=body,
                )
            return body

        if response.status_code == 429:
            raise RateLimitError(
                _message_of(body, response.status_code),
                status=429,
                code=_code_of(body),
                body=body,
                retry_after=_retry_after_seconds(response),
            )
        raise error_from_response(response.status_code, body)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, json: Any | None = None) -> Any:
        return self.request("POST", path, json=json)

    def put(self, path: str, json: Any | None = None) -> Any:
        return self.request("PUT", path, json=json)

    def patch(self, path: str, json: Any | None = None) -> Any:
        return self.request("PATCH", path, json=json)

    def delete(self, path: str, json: Any | None = None) -> Any:
        return self.request("DELETE", path, json=json)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def _message_of(body: Any, status: int) -> str:
    if isinstance(body, dict):
        message = body.get("message")
        if isinstance(message, str) and message:
            return message
        error = body.get("error")
        if isinstance(error, str) and error:
            return error
    return f"HTTP {status}"


def _code_of(body: Any) -> str | None:
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, str):
            return error
    return None


def unwrap(body: Any) -> Any:
    """Peel the ``{"data": ...}`` envelope the API wraps most responses in.

    Some endpoints (``POST /posts``, ``GET /posts/{id}``) return the resource
    bare, so the envelope is unwrapped only when it is actually there.
    """
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body
