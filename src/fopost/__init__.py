"""fopost — official Python SDK for the FoPost API.

Quick start::

    from fopost import Fopost

    client = Fopost(api_key="fp_...")

    accounts = client.accounts.list(workspace_id="9b2f6c1e-...")
    post = client.posts.create(
        workspace_id="9b2f6c1e-...",
        content="Hello from Python",
        accounts=[a.id for a in accounts],
    )
    client.posts.publish(post.id)
"""

from ._http import DEFAULT_BASE_URL
from .client import Fopost
from .errors import (
    AuthenticationError,
    NotFoundError,
    FopostError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
)
from .models import (
    PLATFORMS,
    POST_STATUSES,
    AiCreditBalance,
    AiCredits,
    CaptionResult,
    ContentBlock,
    Delivery,
    Label,
    MediaItem,
    Page,
    PageMeta,
    Platform,
    Post,
    PostAccount,
    PostStatus,
    RepurposeResult,
    RewriteResult,
    RewriteVariant,
    SocialAccount,
    Workspace,
)

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("fopost")
except PackageNotFoundError:  # running from a source tree
    __version__ = "0.0.0"

#: Alias for people arriving from the TypeScript SDK, where the class is `FoPost`.
FoPost = Fopost

__all__ = [
    "DEFAULT_BASE_URL",
    "PLATFORMS",
    "POST_STATUSES",
    "AiCreditBalance",
    "AiCredits",
    "AuthenticationError",
    "CaptionResult",
    "ContentBlock",
    "Delivery",
    "Label",
    "MediaItem",
    "NotFoundError",
    "FoPost",
    "Fopost",
    "FopostError",
    "Page",
    "PageMeta",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "Platform",
    "Post",
    "PostAccount",
    "PostStatus",
    "RateLimitError",
    "RepurposeResult",
    "RewriteResult",
    "RewriteVariant",
    "SocialAccount",
    "Workspace",
    "__version__",
]
