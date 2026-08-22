"""owlstack — official Python SDK for the OwlStack API.

Quick start::

    from owlstack import Owlstack

    client = Owlstack(api_key="osk_...")

    accounts = client.accounts.list(workspace_id="9b2f6c1e-...")
    post = client.posts.create(
        workspace_id="9b2f6c1e-...",
        content="Hello from Python",
        accounts=[a.id for a in accounts],
    )
    client.posts.publish(post.id)
"""

from ._http import DEFAULT_BASE_URL
from .client import Owlstack
from .errors import (
    AuthenticationError,
    NotFoundError,
    OwlstackError,
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

__version__ = "0.1.0"

#: Alias for people arriving from the TypeScript SDK, where the class is `OwlStack`.
OwlStack = Owlstack

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
    "OwlStack",
    "Owlstack",
    "OwlstackError",
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
