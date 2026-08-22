"""Exceptions raised by the SDK.

Every non-2xx response becomes an ``FopostError``. The API answers with an
``{"error": "<code>", "message": "<human readable>"}`` envelope, which maps onto
the ``code`` and ``message`` attributes.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "FopostError",
    "AuthenticationError",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "NotFoundError",
    "RateLimitError",
    "error_from_response",
]


class FopostError(Exception):
    """Base class for every error returned by the FoPost API."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.body = body

    def __str__(self) -> str:
        suffix = f" ({self.code})" if self.code else ""
        return f"[{self.status}{suffix}] {self.message}"


class AuthenticationError(FopostError):
    """401 — missing, invalid, or expired API key."""


class PaymentRequiredError(FopostError):
    """402 — no active subscription, or AI credits exhausted.

    ``upgrade_url`` carries the path the API suggests sending the user to.
    """

    @property
    def upgrade_url(self) -> str | None:
        if isinstance(self.body, dict):
            value = self.body.get("upgrade_url")
            if isinstance(value, str):
                return value
        return None


class PermissionDeniedError(FopostError):
    """403 — the key is valid but lacks the scope or workspace access."""


class NotFoundError(FopostError):
    """404 — no such resource, or it is outside the key's reach."""


class RateLimitError(FopostError):
    """429 — rate limit exceeded. ``retry_after`` is in seconds when sent."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str | None = None,
        body: Any = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status=status, code=code, body=body)
        self.retry_after = retry_after


_BY_STATUS: dict[int, type[FopostError]] = {
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    429: RateLimitError,
}


def error_from_response(
    status: int,
    body: Any,
    *,
    retry_after: float | None = None,
) -> FopostError:
    """Build the most specific error class for a failed response."""
    code: str | None = None
    message = f"HTTP {status}"

    if isinstance(body, dict):
        raw_error = body.get("error")
        if isinstance(raw_error, str):
            code = raw_error
        raw_message = body.get("message")
        if isinstance(raw_message, str) and raw_message:
            message = raw_message
        elif code:
            message = code
    elif isinstance(body, str) and body.strip():
        message = body.strip()

    cls = _BY_STATUS.get(status, FopostError)
    if cls is RateLimitError:
        return RateLimitError(message, status=status, code=code, body=body, retry_after=retry_after)
    return cls(message, status=status, code=code, body=body)
